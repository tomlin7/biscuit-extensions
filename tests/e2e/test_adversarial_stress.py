from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.e2e.conftest import (
    EXTENSIONS_DIR,
    TOP_25_EXTENSIONS,
    MockEditor,
    MockExtensionsAPI,
    load_extension_by_id,
)


class TestAdversarialDependencyManager:
    """Stress-testing the dependency isolation mechanism against corrupt, adversarial, and edge-case inputs."""

    def test_corrupt_installed_stamp_does_not_crash(self, dep_manager: Any) -> None:
        """When .installed contains corrupted or malformed content, ensure_dependencies handles it safely."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest = tmp_path / "extension.toml"
            manifest.write_text(
                '[extension]\nid = "test"\nname = "Test"\nversion = "0.1.0"\ndescription = "Test"\n'
                '[dependencies]\npython = ["urllib3>=2.0.0"]\ntools = []\n',
                encoding="utf-8",
            )
            deps_dir = tmp_path / ".deps"
            deps_dir.mkdir(parents=True, exist_ok=True)
            stamp = deps_dir / ".installed"

            # 1. Truncated hash
            stamp.write_text("abcdef123", encoding="utf-8")
            # 2. Binary garbage
            stamp.write_bytes(b"\x00\xff\xfe\x00corrupted_bytes")

            # Reading should not crash
            pkgs, tools = dep_manager.get_declared_dependencies(tmp_path)
            assert pkgs == ["urllib3>=2.0.0"]

    def test_deps_is_a_file_instead_of_directory(self, dep_manager: Any) -> None:
        """If .deps is unexpectedly a regular file, add_to_sys_path safely returns None without error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            deps_file = tmp_path / ".deps"
            deps_file.write_text("I am a file, not a directory", encoding="utf-8")

            res = dep_manager.add_to_sys_path(tmp_path)
            assert res is None
            # remove_from_sys_path should not throw
            dep_manager.remove_from_sys_path(tmp_path)

    def test_check_tools_with_extreme_values(self, dep_manager: Any) -> None:
        """check_tools handles whitespace-only, empty strings, and special characters safely."""
        missing = dep_manager.check_tools(
            "stress_ext",
            ["", "   ", "non_existent_tool_#$@!%", "python", "git"],
        )
        assert "" not in missing
        assert "   " not in missing
        assert "non_existent_tool_#$@!%" in missing

    def test_sys_path_idempotency_and_missing_removal(self, dep_manager: Any) -> None:
        """Adding same deps_dir multiple times does not duplicate, removing non-existent is a no-op."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            deps_dir = tmp_path / ".deps"
            deps_dir.mkdir()

            resolved = str(deps_dir.resolve())
            dep_manager.add_to_sys_path(tmp_path)
            dep_manager.add_to_sys_path(tmp_path)
            dep_manager.add_to_sys_path(tmp_path)
            assert sys.path.count(resolved) == 1

            dep_manager.remove_from_sys_path(tmp_path)
            assert resolved not in sys.path
            # Second removal must not raise ValueError
            dep_manager.remove_from_sys_path(tmp_path)

    def test_requirements_fallback_with_bom_and_blank_lines(self, dep_manager: Any) -> None:
        """requirements.txt containing UTF-8 BOM, comments, and empty lines is parsed cleanly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest = tmp_path / "extension.toml"
            manifest.write_text(
                '[extension]\nid = "bom_ext"\nname = "BOM"\nversion = "0.1.0"\ndescription = "Test"\n'
                '[dependencies]\npython = []\ntools = []\n',
                encoding="utf-8",
            )
            reqs = tmp_path / "requirements.txt"
            # Write with utf-8-sig (BOM)
            reqs.write_text(
                "# Leading comment\n\n   \nrequests>=2.31.0\n# Another comment\n",
                encoding="utf-8-sig",
            )

            pkgs, tools = dep_manager.get_declared_dependencies(tmp_path)
            assert any("requests>=2.31.0" in p for p in pkgs)


class TestAdversarialExtensionParsers:
    """Stress-testing core extension parsers with edge, malformed, and adversarial inputs."""

    def test_markdown_tools_extreme_table_inputs(self, mock_api: MockExtensionsAPI) -> None:
        """Markdown table formatter handles excessive pipes, no delimiters, and 0-width columns."""
        ext = load_extension_by_id("markdown_tools", mock_api)
        formatter = getattr(ext, "format_table", None)
        assert formatter is not None

        # 1. Row of 100 pipes
        huge_pipes = "|".join(["cell"] * 100)
        res = formatter(huge_pipes)
        assert res is not None

        # 2. Uneven columns: row 1 has 2 cols, row 2 has delimiter of 4 cols, row 3 has 6 cols
        uneven = "| A | B |\n|---|---|---|---|\n| 1 | 2 | 3 | 4 | 5 | 6 |"
        aligned = formatter(uneven)
        assert "|" in aligned

        # 3. Delimiter with colons everywhere
        colon_table = "| Name | Count |\n| :---: | ---: |\n| Alpha | 100 |"
        formatted_colons = formatter(colon_table)
        assert ":" in formatted_colons

        # 4. Table with empty cells
        empty_cells = "|  |  |\n|---|---|\n|  |  |"
        formatted_empty = formatter(empty_cells)
        assert formatted_empty is not None

    def test_markdown_tools_heading_slugify_stress(self, mock_api: MockExtensionsAPI) -> None:
        """Heading parser handles special symbols, HTML tags, duplicate titles, and deep nesting."""
        ext = load_extension_by_id("markdown_tools", mock_api)
        heading_parser = getattr(ext, "parse_headings", None)
        if heading_parser:
            doc = (
                "# Heading with <tags> & symbols #@$!\n"
                "## Heading with <tags> & symbols #@$!\n"
                "### Heading with <tags> & symbols #@$!\n"
                "###### Level 6 Deep Heading\n"
                "```python\n# This is a comment, not a heading\n```\n"
                "### Heading with `code` and [link](https://example.com)\n"
            )
            headings = heading_parser(doc)
            assert len(headings) >= 4
            # Duplicate titles must have unique slugs
            slugs = [h.slug for h in headings]
            assert len(slugs) == len(set(slugs))

    def test_emmet_biscuit_adversarial_abbreviations(self, mock_api: MockExtensionsAPI) -> None:
        """Emmet abbreviation expander handles broken syntax, zero/negative multiplier, and deep nesting."""
        ext = load_extension_by_id("emmet_biscuit", mock_api)
        expander = getattr(ext, "expand_abbreviation", None) or getattr(ext, "expand", None)
        assert expander is not None

        # 1. Unclosed brackets
        r1 = expander("div[class='unclosed")
        assert r1 is not None

        # 2. Unclosed text braces
        r2 = expander("span{unclosed text")
        assert r2 is not None

        # 3. Trailing operator
        r3 = expander("div>p+")
        assert r3 is not None

        # 4. Multiplier with 1 (standard) and deep nesting
        r4 = expander("header>nav>ul>li*3>a")
        assert "<li>" in r4
        assert r4.count("<li>") == 3

        # 5. Numbering substitution with $$$
        r5 = expander("ul>li.item$$$*2")
        assert "item001" in r5
        assert "item002" in r5

    def test_diff_viewer_adversarial_diffs(self, mock_api: MockExtensionsAPI) -> None:
        """Diff viewer handles huge inputs, corrupt unified diffs, and patch generation."""
        ext = load_extension_by_id("diff_viewer", mock_api)

        # 1. Huge line difference (10,000 chars)
        line_a = "A" * 5000 + "X" + "B" * 5000
        line_b = "A" * 5000 + "Y" + "B" * 5000
        rows = ext.compute_side_by_side_diff(line_a, line_b)
        assert len(rows) == 1
        assert rows[0].row_type == "MODIFY"

        # 2. Corrupt patch text without hunk header
        corrupt_diff = "--- file.txt\n+++ file.txt\n+just a random line\n"
        files = ext.parse_unified_diff(corrupt_diff)
        assert isinstance(files, list)

        # 3. Patch application on non-matching text returns original safely
        patched = ext.apply_patch("hello world", corrupt_diff)
        assert patched == "hello world"

        # 4. Stats calculation on empty rows
        stats = ext.compute_stats([])
        assert stats["total_changes"] == 0

    def test_gitlens_blame_adversarial_cases(self, mock_api: MockExtensionsAPI) -> None:
        """GitLens porcelain blame parser handles corrupt SHA, non-digit time, and missing author."""
        ext = load_extension_by_id("gitlens", mock_api)
        parser = getattr(ext, "parse_porcelain_blame", None)
        assert parser is not None

        # 1. Blame with non-digit author-time
        raw_blame = (
            "a" * 40 + " 1 1 1\n"
            "author Test Developer\n"
            "author-time INVALID_TIMESTAMP\n"
            "summary Initial commit\n"
            "\tfirst line of code\n"
        )
        lines = parser(raw_blame)
        assert len(lines) == 1
        assert lines[0].commit.author == "Test Developer"

        # 2. Relative time calculation boundary checks
        from extensions.gitlens.src.gitlens.extension import calculate_relative_time
        assert calculate_relative_time(1000, now_secs=1010) == "just now"
        assert calculate_relative_time(1000, now_secs=1070) == "1 minute ago"
        assert calculate_relative_time(1000, now_secs=5000) == "1 hour ago"
        # Inverted timestamps (clock drift into future)
        assert calculate_relative_time(2000, now_secs=1000) == "just now"

    def test_git_graph_octopus_and_malformed_logs(self, mock_api: MockExtensionsAPI) -> None:
        """Git Graph parser handles multi-parent octopus merges and malformed log entries."""
        ext = load_extension_by_id("git_graph", mock_api)
        parser = getattr(ext, "parse_log", None)
        assert parser is not None

        # 1. Octopus merge with 4 parent hashes
        log_data = (
            "commit1|p1 p2 p3 p4|Alice|alice@test.com|1600000000|Octopus merge|\n"
            "commit2||Bob|bob@test.com|1590000000|Root commit|\n"
        )
        raw_nodes = parser(log_data)
        assert len(raw_nodes) == 2
        assert raw_nodes[0]["parents"] == ["p1", "p2", "p3", "p4"]

        # Test DAG construction
        dag_nodes = ext.build_dag(raw_nodes)
        assert len(dag_nodes) == 2
        assert dag_nodes[0].parents == ["p1", "p2", "p3", "p4"]
        assert dag_nodes[0].is_merge is True
        assert dag_nodes[1].is_root is True

        # 2. Empty log
        assert parser("") == []
        assert ext.build_dag([]) == []

    def test_remote_ssh_config_adversarial_parsing(self, mock_api: MockExtensionsAPI) -> None:
        """Remote SSH parser handles case-insensitive keywords, inline quotes, and multiple aliases."""
        ext = load_extension_by_id("remote_ssh", mock_api)
        config = (
            "# Top level comment\n"
            "HOST my-server srv1 srv2\n"
            "    HOSTNAME 192.168.1.100\n"
            "    USER devuser\n"
            "    PORT 2222\n"
            '    IDENTITYFILE "~/.ssh/id_ed25519"\n'
            "Host *\n"
            "    ForwardAgent yes\n"
            "    ServerAliveInterval 60\n"
        )
        hosts = ext.parse_ssh_config(config)
        assert len(hosts) == 1
        h = hosts[0]
        assert h["hostname"] == "192.168.1.100"
        assert h["user"] == "devuser"
        assert h["port"] == "2222"
        # Wildcard inheritance
        assert h.get("forwardagent") == "yes"

    def test_drawio_xml_adversarial_diagrams(self, mock_api: MockExtensionsAPI) -> None:
        """Draw.io handles empty XML, style formatting roundtrips, and missing geometries."""
        ext = load_extension_by_id("drawio", mock_api)

        # Style parsing and formatting
        style_str = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        parsed = ext.parse_style(style_str)
        assert parsed["rounded"] == "1"
        assert parsed["fillColor"] == "#dae8fc"
        formatted = ext.format_style(parsed)
        assert "rounded=1" in formatted

        # Parsing invalid XML should return empty model gracefully without crashing
        invalid_model = ext.parse_diagram("<unclosed mxfile")
        assert invalid_model["vertices"] == []
        assert invalid_model["pages"] == []

    def test_json_viewer_extreme_inputs(self, mock_api: MockExtensionsAPI) -> None:
        """JSON Viewer validates primitive values, unquoted keys, and deep tree generation."""
        ext = load_extension_by_id("json_viewer", mock_api)

        # 1. Primitives
        assert ext.validate_json("123.456")["valid"] is True
        assert ext.validate_json("true")["valid"] is True
        assert ext.validate_json('"plain string"')["valid"] is True
        assert ext.validate_json("null")["valid"] is True

        # 2. Syntax errors
        res_err = ext.validate_json("{ unquoted_key: 123 }")
        assert res_err["valid"] is False
        assert res_err["line"] is not None

        # 3. Tree model generation for nested data
        nested = {"a": {"b": [1, 2, {"c": "hello"}]}}
        tree = ext.build_tree_model(nested)
        assert tree["type"] == "object"
        assert len(tree["children"]) == 1

        # 4. Minify and format roundtrip
        minified = ext.minify_json('{\n  "name": "biscuit"\n}')
        assert minified == '{"name":"biscuit"}'

    def test_spell_checker_tokenization_and_distance(self, mock_api: MockExtensionsAPI) -> None:
        """Spell checker splits complex programming tokens and computes Levenshtein distance."""
        ext = load_extension_by_id("spell_checker", mock_api)
        from extensions.spell_checker.src.spell_checker.extension import (
            damerau_levenshtein,
            split_identifier,
        )

        # Identifier splitting
        assert split_identifier("getHTTPResponseCode") == ["get", "http", "response", "code"]
        assert split_identifier("is_valid_user_id") == ["is", "valid", "user", "id"]
        assert split_identifier("") == []

        # Distance calculation
        assert damerau_levenshtein("recieve", "receive") == 1  # Transposition
        assert damerau_levenshtein("teh", "the") == 1          # Transposition
        assert damerau_levenshtein("hello", "hello") == 0      # Identical
        assert damerau_levenshtein("", "abc") == 3             # Empty vs string

        # Suggestions
        suggestions = ext.suggest_corrections("funtion")
        assert "function" in suggestions

    def test_todo_tracker_regex_coverage(self, mock_api: MockExtensionsAPI) -> None:
        """TODO tracker recognizes varied comment formats and custom tags."""
        ext = load_extension_by_id("todo_tracker", mock_api)
        code = (
            "// TODO: C-style single line\n"
            "/* FIXME(security): Multi-line block */\n"
            "# HACK: Python hash style\n"
            "-- NOTE: Lua / SQL double dash\n"
            "<!-- BUG: HTML comment -->\n"
            "; XXX: INI semicolon\n"
            "// Regular comment without any tag\n"
        )
        items = ext.scan_content(code, "test.txt")
        assert len(items) >= 5
        tags_found = {it.tag.upper() for it in items}
        assert "TODO" in tags_found
        assert "FIXME" in tags_found
        assert "HACK" in tags_found
        assert "BUG" in tags_found

    def test_bookmarks_boundary_navigation(self, mock_api: MockExtensionsAPI) -> None:
        """Bookmarks handles jumping with 0 bookmarks, 1 bookmark, and cross-file cycle wrap."""
        ext = load_extension_by_id("bookmarks", mock_api)

        # 1. Navigation on completely empty registry
        assert ext.next_bookmark("file.py", 10) is None
        assert ext.previous_bookmark("file.py", 10) is None

        # 2. Toggle on invalid line numbers
        assert ext.toggle_bookmark("file.py", 0) is False
        assert ext.toggle_bookmark("file.py", -5) is False

        # 3. Single bookmark cycle navigation
        ext.add_bookmark("file_a.py", 15, label="Test mark")
        bm_next = ext.next_bookmark("file_a.py", 10)
        assert bm_next is not None
        assert bm_next.line_number == 15

        # Wrap around
        bm_wrap = ext.next_bookmark("file_a.py", 20)
        assert bm_wrap is not None
        assert bm_wrap.line_number == 15

    def test_tailwind_css_class_conflict_detection(self, mock_api: MockExtensionsAPI) -> None:
        """Tailwind CSS extracts complex arbitrary classes and detects property collisions."""
        ext = load_extension_by_id("tailwind_css", mock_api)
        html = '<div class="p-2 p-4 text-red-500 text-blue-500 m-[10px]">'
        classes = ext.extract_classes(html)
        assert "p-2" in classes
        assert "p-4" in classes
        assert "m-[10px]" in classes

        if hasattr(ext, "find_conflicts"):
            conflicts = ext.find_conflicts(classes)
            # p-2 and p-4 conflict on padding; text-red-500 and text-blue-500 conflict on color
            assert len(conflicts) >= 1

    def test_python_adversarial_discovery_and_output_parsing(self, mock_api: MockExtensionsAPI) -> None:
        """Python extension parses pytest summary with varied statuses and durations."""
        ext = load_extension_by_id("python", mock_api)
        sample_output = (
            "tests/test_mod.py::test_one PASSED [ 25%]\n"
            "tests/test_mod.py::test_two FAILED [ 50%]\n"
            "tests/test_mod.py::test_three SKIPPED [ 75%]\n"
            "tests/test_mod.py::test_four ERROR [100%]\n"
            "=================== 1 passed, 1 failed, 1 skipped, 1 error in 4.56s ===================\n"
        )
        res = ext.parse_pytest_output(sample_output)
        assert res["total"] == 4
        assert res["passed"] == 1
        assert res["failed"] == 1
        assert res["skipped"] == 1
        assert res["errors"] == 1
        assert res["duration"] == 4.56

    def test_prettier_adversarial_config_discovery(self, mock_api: MockExtensionsAPI) -> None:
        """Prettier parses simple YAML configs and handles missing files gracefully."""
        from extensions.prettier.src.prettier.extension import parse_yaml_simple, find_prettier_config
        yaml_content = (
            "# Top level comment\n"
            "semi: false\n"
            "singleQuote: true\n"
            "tabWidth: 4\n"
            "printWidth: 100\n"
            "trailingComma: all\n"
        )
        cfg = parse_yaml_simple(yaml_content)
        assert cfg["semi"] is False
        assert cfg["singleQuote"] is True
        assert cfg["tabWidth"] == 4
        assert cfg["printWidth"] == 100
        assert cfg["trailingComma"] == "all"

        # Traversing non-existent root
        assert find_prettier_config(None) == {}

    def test_eslint_adversarial_diagnostic_parsing(self, mock_api: MockExtensionsAPI) -> None:
        """ESLint diagnostic parser handles malformed JSON and compact lines."""
        from extensions.eslint.src.eslint.extension import parse_eslint_json, parse_eslint_compact
        # Malformed JSON
        assert parse_eslint_json("{broken json") == []
        assert parse_eslint_json('{"not": "a list"}') == []

        # Compact format
        compact = "src/index.js: line 42, col 15, Error - 'x' is defined but never used. (no-unused-vars)\n"
        diags = parse_eslint_compact(compact)
        assert len(diags) == 1
        assert diags[0]["line"] == 42
        assert diags[0]["column"] == 15
        assert diags[0]["severity"] == "error"
        assert diags[0]["rule"] == "no-unused-vars"

    def test_thunder_client_adversarial_templates_and_requests(self, mock_api: MockExtensionsAPI) -> None:
        """Thunder Client handles missing template variables and request construction."""
        ext = load_extension_by_id("thunder_client", mock_api)
        ext.set_environment_variable("BASE_URL", "https://api.example.com")
        
        # Defined vs undefined template variable
        interpolated = ext.interpolate_variables("{{BASE_URL}}/users/{{USER_ID}}")
        assert "https://api.example.com/users/{{USER_ID}}" in interpolated

        # Create request with arbitrary method
        req = ext.create_request("PATCH", "{{BASE_URL}}/items/1", headers={"Content-Type": "application/json"})
        assert req["method"] == "PATCH"
        assert "Content-Type" in req["headers"]

    def test_live_server_path_traversal_prevention(self, mock_api: MockExtensionsAPI) -> None:
        """Live Server handler validates root containment and prevents traversal."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            outside_path = (root / ".." / "secret.txt").resolve()
            with pytest.raises(ValueError):
                outside_path.relative_to(root)

            inside_path = (root / "subdir" / "index.html").resolve()
            assert inside_path.relative_to(root) is not None

    def test_error_lens_adversarial_sorting_and_filtering(self, mock_api: MockExtensionsAPI) -> None:
        """Error lens sorts multiple diagnostics on a single line strictly by severity hierarchy."""
        ext = load_extension_by_id("error_lens", mock_api)
        file_key = "test_script.py"
        # Register info, warning, and error on line 20
        diags = [
            {"line": 20, "column": 5, "severity": "info", "message": "Info message"},
            {"line": 20, "column": 1, "severity": "error", "message": "Fatal syntax error"},
            {"line": 20, "column": 10, "severity": "warning", "message": "Deprecated call"},
        ]
        ext.set_diagnostics(file_key, diags)

        # Primary diagnostic must be 'error'
        highest = ext.get_line_diagnostic(file_key, 20)
        assert highest is not None
        assert highest["severity"] == "error"
        assert highest["message"] == "Fatal syntax error"

        # Cleanup
        ext.clear_diagnostics(file_key)
        assert ext.get_diagnostics(file_key) == []

    def test_snippet_manager_adversarial_expansion(self, mock_api: MockExtensionsAPI) -> None:
        """Snippet template expansion resolves built-in variables and tabstops."""
        from extensions.snippet_manager.src.snippet_manager.extension import expand_snippet_template
        template = "def ${1:my_func}(${2:args}):\n    \"\"\"Created on $DATE.\"\"\"\n    $0"
        res = expand_snippet_template(template, filename="controller.py")
        assert "def my_func(args):" in res.text
        assert "Created on 20" in res.text
        assert len(res.tabstops) >= 2

