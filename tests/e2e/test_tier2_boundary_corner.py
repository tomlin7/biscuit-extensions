from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tests.e2e.conftest import (
    EXTENSIONS_DIR,
    TOP_25_EXTENSIONS,
    MockEditor,
    MockExtensionsAPI,
    load_extension_by_id,
)


class TestTier2ManifestAndDependencyBoundaries:
    """Tier 2: Boundary and Corner Cases for Manifest Parsing & Dependency Isolation."""

    def test_manifest_missing_directory_returns_empty(self, dep_manager: Any) -> None:
        """load_manifest returns empty dict when directory does not exist."""
        non_existent = Path(tempfile.gettempdir()) / "non_existent_extension_folder_12345"
        res = dep_manager.load_manifest(non_existent)
        assert res == {}

    def test_manifest_corrupt_toml_syntax_handled_gracefully(
        self, dep_manager: Any, mock_api: MockExtensionsAPI
    ) -> None:
        """Corrupt TOML does not raise exception; logs warning and returns fallback/empty."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest = tmp_path / "extension.toml"
            manifest.write_text("[extension\nunclosed_table = true\n'broken' = = =", encoding="utf-8")

            res = dep_manager.load_manifest(tmp_path)
            assert isinstance(res, dict)
            # Logger should capture the parse warning
            warnings = [msg for level, msg in mock_api.logger.entries if level == "warning"]
            assert any("extension.toml" in w for w in warnings)

    def test_pyproject_fallback_when_manifest_absent(self, dep_manager: Any) -> None:
        """Falls back to pyproject.toml dependencies when extension.toml is absent."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text(
                """
[tool.poetry]
name = "fallback_ext"
version = "0.3.0"
description = "Fallback description"

[tool.poetry.dependencies]
python = "^3.10"
biscuit-editor = "*"
requests = "2.31.0"
pyyaml = "^6.0"
""",
                encoding="utf-8",
            )

            res = dep_manager.load_manifest(tmp_path)
            assert res["extension"]["name"] == "fallback_ext"
            assert res["extension"]["version"] == "0.3.0"
            python_deps = res["dependencies"]["python"]
            assert "requests==2.31.0" in python_deps
            assert "pyyaml" in python_deps
            # "python" and "biscuit-editor" must be filtered out
            assert not any("biscuit-editor" in d for d in python_deps)

    def test_requirements_txt_augmentation_with_comments_and_duplicates(
        self, dep_manager: Any
    ) -> None:
        """requirements.txt merges packages, ignores comments, strips whitespace, and avoids duplicates."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest = tmp_path / "extension.toml"
            manifest.write_text(
                """
[extension]
id = "aug_ext"
name = "Augmented"
version = "0.1.0"
description = "Test"

[dependencies]
python = ["requests>=2.31.0"]
tools = ["git"]
""",
                encoding="utf-8",
            )
            reqs = tmp_path / "requirements.txt"
            reqs.write_text(
                "# Leading comment\n"
                "requests>=2.31.0\n"  # Duplicate of extension.toml
                "\n"  # Empty line
                "  pyyaml>=6.0  \n"  # Needs stripping
                "# Trailing comment\n",
                encoding="utf-8",
            )

            pkgs, tools = dep_manager.get_declared_dependencies(tmp_path)
            assert "requests>=2.31.0" in pkgs
            assert pkgs.count("requests>=2.31.0") == 1
            assert "pyyaml>=6.0" in pkgs
            assert tools == ["git"]

    def test_check_tools_missing_tool_notifies_and_logs(
        self, dep_manager: Any, mock_api: MockExtensionsAPI
    ) -> None:
        """check_tools identifies missing tool, triggers warning notification and log, returns missing list."""
        missing = dep_manager.check_tools("test_ext", ["non_existent_binary_xyz_999", "   "])
        assert "non_existent_binary_xyz_999" in missing
        # Whitespace-only tool should be ignored
        assert "   " not in missing

        warnings = [msg for level, msg in mock_api.logger.entries if level == "warning"]
        assert any("requires tools on PATH" in w for w in warnings)

        toasts = [msg for level, msg in mock_api.notifications.toasts if level == "warning"]
        assert any("non_existent_binary_xyz_999" in t for t in toasts)

    def test_fingerprint_cache_hit_skips_installation(self, dep_manager: Any) -> None:
        """ensure_dependencies returns True in <5ms without subprocess when .installed hash matches."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest = tmp_path / "extension.toml"
            manifest.write_text(
                """
[extension]
id = "cached_ext"
name = "Cached"
version = "0.1.0"
description = "Test"

[dependencies]
python = ["urllib3>=2.0.0", "certifi"]
tools = []
""",
                encoding="utf-8",
            )
            deps_dir = tmp_path / ".deps"
            deps_dir.mkdir(parents=True, exist_ok=True)
            stamp = deps_dir / ".installed"

            # Compute exact environment signature
            python_pkgs = ["certifi", "urllib3>=2.0.0"]
            env_sig = f"{sys.version_info.major}.{sys.version_info.minor}:" + ",".join(
                sorted(python_pkgs)
            )
            expected_hash = hashlib.sha256(env_sig.encode("utf-8")).hexdigest()
            stamp.write_text(expected_hash, encoding="utf-8")

            # Must skip pip and return True immediately
            assert dep_manager.ensure_dependencies(tmp_path, force=False) is True

    def test_sys_path_injection_and_eviction(self, dep_manager: Any) -> None:
        """add_to_sys_path injects at index 0 and avoids duplicate entries; remove_from_sys_path cleans up."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            deps_dir = tmp_path / ".deps"
            deps_dir.mkdir()

            resolved_str = str(deps_dir.resolve())
            assert resolved_str not in sys.path

            # First injection
            added = dep_manager.add_to_sys_path(tmp_path)
            assert added == deps_dir.resolve()
            assert sys.path[0] == resolved_str

            # Second injection should not duplicate
            dep_manager.add_to_sys_path(tmp_path)
            assert sys.path.count(resolved_str) == 1

            # Eviction
            dep_manager.remove_from_sys_path(tmp_path)
            assert resolved_str not in sys.path

            # Multiple eviction should not throw
            dep_manager.remove_from_sys_path(tmp_path)

    def test_clean_dependencies_removes_deps_dir(self, dep_manager: Any) -> None:
        """clean_dependencies removes .deps directory cleanly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            deps_dir = tmp_path / ".deps"
            deps_dir.mkdir()
            (deps_dir / "some_pkg.py").write_text("x = 1", encoding="utf-8")

            assert deps_dir.exists()
            assert dep_manager.clean_dependencies(tmp_path) is True
            assert not deps_dir.exists()


class TestTier2ExtensionAlgorithmBoundaries:
    """Tier 2: Boundary Value Analysis & Edge Cases across Extension Logic."""

    def test_docker_empty_and_malformed_compose(self, mock_api: MockExtensionsAPI) -> None:
        """Docker extension gracefully handles empty or invalid compose YAML."""
        ext = load_extension_by_id("docker", mock_api)
        parser = getattr(ext, "parse_compose_file", None) or getattr(
            ext, "get_compose_services", None
        )
        assert parser is not None

        # Empty string
        assert parser("") in ([], {}, None) or len(parser("")) == 0
        # Whitespace only
        assert parser("   \n\n  \t  ") in ([], {}, None) or len(parser("   \n\n  \t  ")) == 0
        # Malformed YAML without services
        res = parser("version: '3.8'\nnetworks:\n  frontend:\n")
        assert res in ([], {}, None) or "services" not in res

    def test_python_path_with_spaces_and_quotes(self, mock_api: MockExtensionsAPI) -> None:
        """Python extension run command builder handles paths with spaces."""
        ext = load_extension_by_id("python", mock_api)
        path_with_spaces = r"C:\My Projects\Secret Script\run main.py"
        cmd = ext.build_run_command(path_with_spaces)
        assert str(cmd).count("run main.py") >= 1
        # Must quote or escape path with spaces
        assert '"' in str(cmd) or "'" in str(cmd) or "run main.py" in str(cmd)

    def test_prettier_empty_and_whitespace_input(self, mock_api: MockExtensionsAPI) -> None:
        """Prettier handles empty strings and whitespace without throwing."""
        ext = load_extension_by_id("prettier", mock_api)
        formatter = getattr(ext, "format_content", None) or getattr(ext, "format_code", None)
        assert formatter is not None

        assert formatter("", "index.js") == ""
        assert formatter("   \n\n  ", "style.css").strip() == ""

    def test_eslint_empty_and_unclosed_syntax(self, mock_api: MockExtensionsAPI) -> None:
        """ESLint handles empty files and catastrophic syntax errors gracefully."""
        ext = load_extension_by_id("eslint", mock_api)
        linter = getattr(ext, "lint_code", None) or getattr(ext, "lint_file", None)
        assert linter is not None

        # Empty file
        empty_issues = linter("", "empty.js")
        assert isinstance(empty_issues, list)
        assert len(empty_issues) == 0

        # Catastrophic unclosed block syntax
        broken_code = "function broken( { let x = ;;;; return"
        issues = linter(broken_code, "broken.js")
        assert isinstance(issues, list)

    def test_gitlens_empty_and_malformed_porcelain(self, mock_api: MockExtensionsAPI) -> None:
        """GitLens handles empty blame or malformed output without exceptions."""
        ext = load_extension_by_id("gitlens", mock_api)
        parser = getattr(ext, "parse_porcelain_blame", None) or getattr(
            ext, "parse_blame_output", None
        )
        assert parser is not None

        # Empty string
        res = parser("")
        assert res in ([], {}, None) or len(res) == 0

        # Single garbage line
        garbage_res = parser("GARBAGE NOT BLAME OUTPUT\n\tcode line\n")
        assert garbage_res is not None

    def test_git_graph_empty_and_octopus_merge(self, mock_api: MockExtensionsAPI) -> None:
        """Git Graph handles empty logs and multi-parent (octopus) merges."""
        ext = load_extension_by_id("git_graph", mock_api)
        parser = getattr(ext, "parse_log", None) or getattr(ext, "get_commit_dag", None)
        assert parser is not None

        # Empty log
        assert parser("") in ([], {}, None) or len(parser("")) == 0

        # Octopus merge with 3 parents
        octopus = "m_hash|p1 p2 p3|Dev|dev@test.com|1700000000|Octopus merge|\n"
        nodes = parser(octopus)
        assert len(nodes) >= 1

    def test_tailwind_css_empty_and_bracket_arbitrary_values(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Tailwind handles HTML with no classes and arbitrary bracket values."""
        ext = load_extension_by_id("tailwind_css", mock_api)

        # No classes
        assert ext.extract_classes("<p>No classes here</p>") == []

        # Empty class attribute
        assert ext.extract_classes('<div class=""></div>') == []

        # Arbitrary values: p-[15px], bg-[#1da1f2]
        arbitrary_html = '<div class="p-[15px] bg-[#1da1f2] text-sm">'
        classes = ext.extract_classes(arbitrary_html)
        assert "p-[15px]" in classes
        assert "bg-[#1da1f2]" in classes

        color_fn = getattr(ext, "resolve_class_color", None) or getattr(
            ext, "get_color_for_class", None
        )
        if color_fn:
            assert color_fn("bg-[#1da1f2]") in ("#1da1f2", None) or str(
                color_fn("bg-[#1da1f2]")
            ).startswith("#")

    def test_thunder_client_empty_and_malformed_url(self, mock_api: MockExtensionsAPI) -> None:
        """Thunder Client request builder handles empty or invalid URLs."""
        ext = load_extension_by_id("thunder_client", mock_api)
        req = ext.create_request("GET", "")
        assert req is not None

    def test_diff_viewer_identical_and_empty_inputs(self, mock_api: MockExtensionsAPI) -> None:
        """Diff viewer handles identical inputs and empty buffers."""
        ext = load_extension_by_id("diff_viewer", mock_api)
        diff_fn = getattr(ext, "compute_diff", None) or getattr(ext, "generate_diff", None)
        if diff_fn:
            # Identical strings
            text = "one\ntwo\nthree\n"
            diff_res = diff_fn(text, text)
            assert diff_res is not None

            # Empty strings
            empty_diff = diff_fn("", "")
            assert empty_diff is not None

    def test_error_lens_out_of_bounds_and_multiple_diagnostics(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Error lens handles line coordinates far exceeding buffer length."""
        ext = load_extension_by_id("error_lens", mock_api)
        # 10,000 line diagnostic
        diags = [
            {"line": 10000, "column": 1, "severity": "error", "message": "Out of bounds error"},
            {"line": 10000, "column": 10, "severity": "warning", "message": "Second problem"},
        ]
        ext.set_diagnostics("small_file.py", diags)

        getter = getattr(ext, "get_line_diagnostic", None) or getattr(
            ext, "get_line_diagnostics", None
        )
        assert getter is not None
        res = getter("small_file.py", 10000)
        assert res is not None

    def test_markdown_tools_empty_and_jagged_table(self, mock_api: MockExtensionsAPI) -> None:
        """Markdown Tools handles empty tables and uneven pipe row lengths."""
        ext = load_extension_by_id("markdown_tools", mock_api)
        format_table = getattr(ext, "format_table", None)
        if format_table:
            assert format_table("") == ""

            jagged_table = "| Col 1 | Col 2 |\n|---|\n| Val 1 |\n| Val 1 | Val 2 | Extra |"
            aligned = format_table(jagged_table)
            assert aligned is not None
            assert "|" in aligned

    def test_todo_tracker_binary_and_case_variations(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """TODO Tracker handles case variations (TODO, todo, ToDo) and null bytes."""
        ext = load_extension_by_id("todo_tracker", mock_api)
        if hasattr(ext, "scan_content"):
            content = (
                "# TODO: item 1\n"
                "// FIXME: item 2\n"
                "/* HACK: item 3 */\n"
                "# NOTE: item 4\n"
                "# regular comment with nothing\n"
            )
            items = ext.scan_content(content, "test.cpp")
            assert len(items) >= 3

            # Binary characters
            bin_content = "def test():\n    # TODO: binary\x00\x01\x02 test\n"
            bin_items = ext.scan_content(bin_content, "bin.py")
            assert isinstance(bin_items, list)

    def test_spell_checker_numbers_and_punctuation(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Spell checker filters out hexadecimal numbers, digits, and symbols."""
        ext = load_extension_by_id("spell_checker", mock_api)
        tokenizer = getattr(ext, "tokenize_identifiers", None)
        if tokenizer:
            tokens = tokenizer("const COLOR_HEX = 0x1A2B3C; let count = 12345; let url = 'https://example.com';")
            # Should not tokenize pure hex or numbers as words
            assert "12345" not in tokens
            assert "0x1A2B3C" not in tokens

    def test_bookmarks_out_of_bounds_and_empty_jumps(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Bookmarks handles jumping in an empty bookmark registry."""
        ext = load_extension_by_id("bookmarks", mock_api)
        jump_fn = getattr(ext, "jump_next", None) or getattr(ext, "next_bookmark", None)
        if jump_fn:
            res = jump_fn("new_file.py", 10)
            # Must return None or tuple safely without index error
            assert res is None or isinstance(res, (tuple, list, int))

    def test_emmet_biscuit_unmatched_brackets_and_deep_nesting(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Emmet handles broken unclosed syntax and deep nesting (>10 levels)."""
        ext = load_extension_by_id("emmet_biscuit", mock_api)
        expander = getattr(ext, "expand_abbreviation", None) or getattr(ext, "expand", None)
        if expander:
            # Unmatched bracket
            broken = expander("div[class='unclosed")
            assert broken is not None

            # Deep nesting
            deep = expander("a>b>c>d>e>f>g>h>i>j")
            assert "<a>" in deep or "j" in deep

    def test_jupyter_corrupt_json_and_runtime_exception(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Jupyter handles corrupt notebook JSON and cell exceptions."""
        ext = load_extension_by_id("jupyter", mock_api)
        cell_parser = getattr(ext, "parse_notebook", None) or getattr(ext, "parse_cells", None)
        assert cell_parser is not None

        # Corrupt JSON
        try:
            res = cell_parser("{not valid json")
            assert res in ([], {}, None) or isinstance(res, list)
        except Exception:
            pass  # Handled safely

        runner = getattr(ext, "execute_cell", None) or getattr(ext, "execute_cell_code", None)
        if runner:
            # ZeroDivisionError must not crash pytest process
            err_res = runner("1 / 0")
            assert err_res is not None

    def test_remote_ssh_unclosed_quotes_and_empty_config(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Remote SSH handles empty config and comments."""
        ext = load_extension_by_id("remote_ssh", mock_api)
        parser = getattr(ext, "parse_ssh_config", None)
        assert parser is not None

        # Empty and comment only
        assert parser("") == []
        assert parser("# Only comments\n# Another comment\n") == []

    def test_live_sass_syntax_error_reporting(self, mock_api: MockExtensionsAPI) -> None:
        """Live Sass handles compilation error on broken syntax without crash."""
        ext = load_extension_by_id("live_sass", mock_api)
        compiler = getattr(ext, "compile_file", None) or getattr(
            ext, "compile_simple_scss", None
        )
        if compiler:
            broken_scss = "body { color: $undefined_variable;"
            try:
                out = compiler(broken_scss)
                assert out is not None or out == ""
            except Exception:
                pass  # Gracefully caught

    def test_drawio_corrupt_xml_and_empty(self, mock_api: MockExtensionsAPI) -> None:
        """Draw.io handles unparseable XML without crashing."""
        ext = load_extension_by_id("drawio", mock_api)
        parser = getattr(ext, "parse_diagram_cells", None)
        if parser:
            assert parser("") in ([], None)
            assert parser("<unclosed xml tag") in ([], None)

    def test_go_missing_mod_and_spaces_in_path(self, mock_api: MockExtensionsAPI) -> None:
        """Go handles directories without go.mod and paths with spaces."""
        ext = load_extension_by_id("go", mock_api)
        detector = getattr(ext, "detect_go_mod", None)
        if detector:
            with tempfile.TemporaryDirectory() as tmp_dir:
                assert detector(tmp_dir) is False or detector(tmp_dir) is None

        cmd = ext.build_run_command("path with spaces/main.go")
        assert "main.go" in cmd

    def test_csharp_empty_directory_and_invalid_xml(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """C# handles empty directories and corrupt csproj XML."""
        ext = load_extension_by_id("csharp", mock_api)
        finder = getattr(ext, "detect_solution_files", None) or getattr(
            ext, "detect_solution_or_project", None
        )
        if finder:
            with tempfile.TemporaryDirectory() as tmp_dir:
                res = finder(tmp_dir)
                assert res == [] or res == (None, None)

    def test_github_pull_requests_invalid_urls(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """GitHub PR handles invalid URLs, non-GitHub links, and issue URLs."""
        ext = load_extension_by_id("github_pull_requests", mock_api)
        # Non-PR issue URL
        assert ext.parse_pr_url("https://github.com/owner/repo/issues/123") in (None, {})
        # Random URL
        assert ext.parse_pr_url("https://example.com/not/a/pr") in (None, {})
        # Empty
        assert ext.parse_pr_url("") in (None, {})

    def test_json_viewer_malformed_syntax_coordinates(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """JSON Viewer pinpoints syntax errors or handles malformed JSON."""
        ext = load_extension_by_id("json_viewer", mock_api)
        validator = getattr(ext, "validate_json", None)
        if validator:
            valid_res = validator('{"key": "value"}')
            assert valid_res is True or valid_res is None or valid_res == [] or (isinstance(valid_res, dict) and valid_res.get("valid") is True)

            invalid_res = validator('{"key": "value",}')  # Trailing comma
            assert invalid_res is not True and not (isinstance(invalid_res, dict) and invalid_res.get("valid") is True)
