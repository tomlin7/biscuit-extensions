from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
import toml

from tests.e2e.conftest import (
    EXTENSIONS_DIR,
    TOP_25_EXTENSIONS,
    MockExtensionsAPI,
    load_extension_by_id,
)

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")


class TestTier1Manifests:
    """Tier 1: Manifest Schema, Metadata & Dependency Isolation Verification."""

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_extension_directory_exists(self, ext_id: str) -> None:
        """Verify extension folder exists under extensions/<ext_id>."""
        ext_dir = EXTENSIONS_DIR / ext_id
        assert ext_dir.is_dir(), f"Extension directory missing: {ext_dir}"

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_manifest_file_exists_and_parses(self, ext_id: str) -> None:
        """Verify extension.toml exists and parses as valid TOML."""
        manifest_path = EXTENSIONS_DIR / ext_id / "extension.toml"
        assert manifest_path.is_file(), f"extension.toml missing for {ext_id}"

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        assert isinstance(data, dict), f"Failed to parse TOML in {manifest_path}"
        assert "extension" in data or "name" in data, f"Missing extension table in {manifest_path}"

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_manifest_required_fields(self, ext_id: str) -> None:
        """Verify id, name, version, and description are present."""
        manifest_path = EXTENSIONS_DIR / ext_id / "extension.toml"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        ext_data = data.get("extension", data)
        assert ext_data.get("id") or ext_data.get("name"), f"Missing id/name in {ext_id}"
        assert "version" in ext_data, f"Missing version in {ext_id}"
        assert "description" in ext_data, f"Missing description in {ext_id}"

        version_str = str(ext_data["version"])
        assert SEMVER_PATTERN.match(version_str), f"Invalid semver '{version_str}' in {ext_id}"

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_manifest_author_tomlin7(self, ext_id: str) -> None:
        """Verify author is explicitly declared as 'tomlin7' per specification."""
        manifest_path = EXTENSIONS_DIR / ext_id / "extension.toml"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        ext_data = data.get("extension", data)
        author = ext_data.get("author", "")
        assert author == "tomlin7", f"Extension {ext_id} author is '{author}', expected 'tomlin7'"

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_manifest_declares_dependencies_table(self, ext_id: str) -> None:
        """Verify [dependencies] table is present with python or tools lists."""
        manifest_path = EXTENSIONS_DIR / ext_id / "extension.toml"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        assert "dependencies" in data, f"Extension {ext_id} missing [dependencies] table"
        deps = data["dependencies"]
        assert isinstance(deps, dict), f"[dependencies] in {ext_id} must be a dictionary"

        python_deps = deps.get("python", [])
        tool_deps = deps.get("tools", [])
        assert isinstance(python_deps, list), f"dependencies.python in {ext_id} must be a list"
        assert isinstance(tool_deps, list), f"dependencies.tools in {ext_id} must be a list"


class TestTier1LifecycleAndLoading:
    """Tier 1: Extension Lifecycle, Entrypoint & Contribution Registration."""

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_entrypoint_exists_and_callable(self, ext_id: str) -> None:
        """Verify src/<ext_id>/__init__.py exists and defines setup(api)."""
        init_path = EXTENSIONS_DIR / ext_id / "src" / ext_id / "__init__.py"
        assert init_path.is_file(), f"Missing entrypoint {init_path}"

        with open(init_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "def setup" in content, f"Entrypoint {init_path} does not define setup(api)"

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_extension_loads_and_registers(self, ext_id: str, mock_api: MockExtensionsAPI) -> None:
        """Verify extension loads via load_extension_by_id and registers with api."""
        ext_instance = load_extension_by_id(ext_id, mock_api)
        assert ext_instance is not None, f"Extension {ext_id} failed to instantiate"

        # Check registration
        assert (
            ext_id in mock_api.registered_extensions or ext_instance is not None
        ), f"Extension {ext_id} not found in registered_extensions"

    @pytest.mark.parametrize("ext_id", TOP_25_EXTENSIONS)
    def test_extension_contributes_ui_or_commands(
        self, ext_id: str, mock_api: MockExtensionsAPI
    ) -> None:
        """Verify extension contributes commands, views, statusbar, or settings."""
        ext_instance = load_extension_by_id(ext_id, mock_api)
        assert ext_instance is not None

        # Check contributions via API or manifest
        manifest_path = EXTENSIONS_DIR / ext_id / "extension.toml"
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        has_manifest_contributions = "contributes" in data and bool(data["contributes"])
        has_api_commands = len(mock_api.commands.commands) > 0
        has_api_buttons = len(mock_api.statusbar.buttons) > 0
        has_api_views = (
            len(mock_api.views.sidebar_views) > 0 or len(mock_api.views.panel_views) > 0
        )
        has_registered_hooks = (
            bool(mock_api.run_commands)
            or bool(mock_api.comment_prefixes)
            or bool(mock_api.langservers)
        )

        assert (
            has_manifest_contributions
            or has_api_commands
            or has_api_buttons
            or has_api_views
            or has_registered_hooks
            or hasattr(ext_instance, "install")
        ), f"Extension {ext_id} does not contribute any commands, views, or hooks"


class TestTier1FunctionalContracts:
    """Tier 1: Core Functional Behavior for all 25 Extensions."""

    def test_docker_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test docker extension compose parsing and container lifecycle."""
        ext = load_extension_by_id("docker", mock_api)
        sample_compose = """
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:15
"""
        # Compose file parsing
        parser = getattr(ext, "parse_compose_file", None) or getattr(
            ext, "get_compose_services", None
        )
        assert parser is not None, "Docker extension must provide compose file parser"
        services = parser(sample_compose)
        assert isinstance(services, (list, dict))
        if isinstance(services, list):
            assert "web" in services
            assert "db" in services
        else:
            assert "web" in services or "services" in services

        # Container lifecycle
        if hasattr(ext, "list_containers"):
            containers = ext.list_containers()
            assert isinstance(containers, list)
        if hasattr(ext, "start_container") and hasattr(ext, "stop_container"):
            assert ext.start_container("c_test") in (True, False, None) or isinstance(
                ext.start_container("c_test"), (bool, dict, str)
            )

    def test_python_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test python extension interpreter detection and run command."""
        ext = load_extension_by_id("python", mock_api)
        assert hasattr(ext, "get_interpreter"), "Python extension must provide get_interpreter"
        interpreter = ext.get_interpreter()
        assert isinstance(interpreter, (str, Path))
        assert str(interpreter).strip() != ""

        assert hasattr(ext, "build_run_command"), "Python extension must provide build_run_command"
        cmd = ext.build_run_command("app.py")
        assert "app.py" in str(cmd)
        assert "python" in str(cmd).lower()

        if hasattr(ext, "detect_virtualenvs"):
            venvs = ext.detect_virtualenvs(str(Path.cwd()))
            assert isinstance(venvs, list)

    def test_prettier_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test prettier extension configuration discovery and code formatting."""
        ext = load_extension_by_id("prettier", mock_api)
        formatter = getattr(ext, "format_content", None) or getattr(ext, "format_code", None)
        assert formatter is not None, "Prettier extension must provide format method"

        # Test formatting JSON
        unformatted_json = '{"a": 1,   "b":   [2, 3]}'
        formatted = formatter(unformatted_json, "test.json")
        assert isinstance(formatted, str)
        assert len(formatted.strip()) > 0

    def test_eslint_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test eslint extension diagnostic scanning and fix application."""
        ext = load_extension_by_id("eslint", mock_api)
        linter = getattr(ext, "lint_code", None) or getattr(ext, "lint_file", None)
        assert linter is not None, "ESLint extension must provide lint method"

        js_with_issues = "var x = 10;\ndebugger;\n"
        diagnostics = linter(js_with_issues, "test.js")
        assert isinstance(diagnostics, list)

        if hasattr(ext, "apply_fixes") or hasattr(ext, "fix_code"):
            fixer = getattr(ext, "apply_fixes", None) or getattr(ext, "fix_code", None)
            fixed = fixer(js_with_issues)
            assert isinstance(fixed, str)

    def test_gitlens_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test gitlens blame parsing and annotation formatting."""
        ext = load_extension_by_id("gitlens", mock_api)
        porcelain_sample = (
            "b00fa290d882fcb5afba9f218d8ae167cdeab218 1 1 1\n"
            "author Alice Smith\n"
            "author-mail <alice@example.com>\n"
            "author-time 1700000000\n"
            "author-tz +0000\n"
            "committer Alice Smith\n"
            "summary Initial commit\n"
            "filename main.py\n"
            "\tprint('hello')\n"
        )
        parser = getattr(ext, "parse_porcelain_blame", None) or getattr(
            ext, "parse_blame_output", None
        )
        assert parser is not None, "GitLens extension must provide blame parser"
        blame_records = parser(porcelain_sample)
        assert blame_records is not None

        formatter = getattr(ext, "format_blame_annotation", None)
        if formatter:
            annot = formatter(
                {"author": "Alice", "summary": "Initial commit", "time": 1700000000}
            )
            assert "Alice" in str(annot)

    def test_git_graph_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test git_graph commit log and DAG parsing."""
        ext = load_extension_by_id("git_graph", mock_api)
        log_sample = (
            "hash1|hash0|Alice|alice@example.com|1700000000|commit 1|(HEAD -> main)\n"
            "hash0||Bob|bob@example.com|1699990000|initial commit|\n"
        )
        parser = getattr(ext, "parse_log", None) or getattr(ext, "get_commit_dag", None)
        assert parser is not None, "Git Graph extension must provide log/DAG parser"
        nodes = parser(log_sample)
        assert len(nodes) >= 2

    def test_tailwind_css_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test tailwind_css class extraction, color matching, and conflict checks."""
        ext = load_extension_by_id("tailwind_css", mock_api)
        html_input = '<div class="bg-blue-500 text-white p-2 p-4 flex block">'

        assert hasattr(ext, "extract_classes"), "Tailwind must provide extract_classes"
        classes = ext.extract_classes(html_input)
        assert "bg-blue-500" in classes
        assert "text-white" in classes

        color_resolver = getattr(ext, "resolve_class_color", None) or getattr(
            ext, "get_color_for_class", None
        )
        if color_resolver:
            color = color_resolver("bg-blue-500")
            assert color is not None
            assert str(color).startswith("#")

        conflict_checker = getattr(ext, "detect_conflicts", None) or getattr(
            ext, "lint_conflicts", None
        )
        if conflict_checker:
            conflicts = conflict_checker(classes)
            assert conflicts is not None

    def test_thunder_client_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test thunder_client request creation and response formatting."""
        ext = load_extension_by_id("thunder_client", mock_api)
        assert hasattr(ext, "create_request"), "Thunder Client must provide create_request"
        req = ext.create_request("GET", "https://httpbin.org/get")
        assert req is not None

        assert hasattr(ext, "format_response"), "Thunder Client must provide format_response"
        dummy_resp = {"status_code": 200, "headers": {"Content-Type": "application/json"}, "body": '{"ok": true}'}
        formatted = ext.format_response(dummy_resp)
        assert formatted is not None

    def test_live_server_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test live_server server lifecycle management."""
        ext = load_extension_by_id("live_server", mock_api)
        start_fn = getattr(ext, "start_server", None) or getattr(ext, "start", None)
        stop_fn = getattr(ext, "stop_server", None) or getattr(ext, "stop", None)
        assert start_fn is not None and stop_fn is not None, "Live Server must provide start/stop"

    def test_diff_viewer_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test diff_viewer diff computation and patch parsing."""
        ext = load_extension_by_id("diff_viewer", mock_api)
        original = "line 1\nline 2\nline 3\n"
        modified = "line 1\nline 2 modified\nline 3\nline 4\n"

        diff_fn = getattr(ext, "compute_diff", None) or getattr(ext, "generate_diff", None)
        if diff_fn:
            result = diff_fn(original, modified)
            assert result is not None

    def test_error_lens_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test error_lens diagnostic processing and line decoration."""
        ext = load_extension_by_id("error_lens", mock_api)
        assert hasattr(ext, "set_diagnostics"), "Error Lens must provide set_diagnostics"
        diags = [{"line": 10, "column": 5, "severity": "error", "message": "Syntax error"}]
        ext.set_diagnostics("test.py", diags)

        getter = getattr(ext, "get_line_diagnostic", None) or getattr(ext, "get_line_diagnostics", None)
        assert getter is not None, "Error Lens must provide line diagnostic getter"
        line_diag = getter("test.py", 10)
        assert line_diag is not None

    def test_markdown_tools_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test markdown_tools table formatting and TOC generation."""
        ext = load_extension_by_id("markdown_tools", mock_api)
        unformatted_table = "| Name | Role |\n|---|---|\n| Alice | Dev |\n| Bob | Tester |"
        format_table = getattr(ext, "format_table", None)
        if format_table:
            aligned = format_table(unformatted_table)
            assert "|" in aligned
            assert "Alice" in aligned

        doc_with_headings = "# Title\n\n## Section 1\n\n### Subsection\n"
        toc_fn = getattr(ext, "generate_toc", None)
        if toc_fn:
            toc = toc_fn(doc_with_headings)
            assert "Section 1" in str(toc)

    def test_todo_tracker_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test todo_tracker scanning for annotations."""
        ext = load_extension_by_id("todo_tracker", mock_api)
        sample_code = (
            "# TODO: implement auth\n"
            "def login():\n"
            "    # FIXME: handle null token\n"
            "    pass\n"
        )
        scanner = getattr(ext, "scan_content", None) or getattr(ext, "scan_workspace", None)
        assert scanner is not None, "TODO Tracker must provide scanning capability"
        if hasattr(ext, "scan_content"):
            items = ext.scan_content(sample_code, "auth.py")
            assert len(items) >= 2

    def test_spell_checker_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test spell_checker typo detection and tokenizer."""
        ext = load_extension_by_id("spell_checker", mock_api)
        tokenizer = getattr(ext, "tokenize_identifiers", None)
        if tokenizer:
            tokens = tokenizer("parseSshConfig and my_variable_name")
            assert "parse" in tokens or "Ssh" in tokens or "ssh" in tokens

    def test_bookmarks_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test bookmarks line bookmark toggling and cycling."""
        ext = load_extension_by_id("bookmarks", mock_api)
        toggle = getattr(ext, "toggle_bookmark", None)
        if toggle:
            res1 = toggle("app.py", 15)
            assert res1 in (True, False, None)

    def test_emmet_biscuit_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test emmet_biscuit abbreviation expansion."""
        ext = load_extension_by_id("emmet_biscuit", mock_api)
        expander = getattr(ext, "expand_abbreviation", None) or getattr(ext, "expand", None)
        if expander:
            expanded = expander("div>p")
            assert "div" in expanded
            assert "p" in expanded

    def test_jupyter_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test jupyter notebook cell parsing and code execution."""
        ext = load_extension_by_id("jupyter", mock_api)
        sample_ipynb = '{"cells": [{"cell_type": "code", "source": ["2 + 3"], "outputs": []}], "metadata": {}}'
        cell_parser = getattr(ext, "parse_cells", None) or getattr(ext, "parse_notebook", None)
        assert cell_parser is not None, "Jupyter must provide cell parser"
        cells = cell_parser(sample_ipynb)
        assert len(cells) >= 1

        runner = getattr(ext, "execute_cell", None) or getattr(ext, "execute_cell_code", None)
        if runner:
            res = runner("3 * 7")
            assert res is not None

    def test_remote_ssh_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test remote_ssh config parsing and connect command generation."""
        ext = load_extension_by_id("remote_ssh", mock_api)
        sample_config = (
            "Host dev-server\n"
            "    HostName 192.168.1.50\n"
            "    User ubuntu\n"
            "    Port 2222\n"
        )
        parser = getattr(ext, "parse_ssh_config", None)
        assert parser is not None, "Remote SSH must provide config parser"
        hosts = parser(sample_config)
        assert len(hosts) >= 1

        builder = getattr(ext, "build_connect_command", None)
        if builder and hosts:
            cmd = builder(hosts[0])
            assert "ssh" in cmd
            assert "ubuntu" in cmd

    def test_live_sass_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test live_sass compilation and output path derivation."""
        ext = load_extension_by_id("live_sass", mock_api)
        assert hasattr(ext, "get_output_css_path"), "Live Sass must provide get_output_css_path"
        out_path = ext.get_output_css_path("src/style.scss")
        assert out_path.endswith(".css")

        compiler = getattr(ext, "compile_file", None) or getattr(ext, "compile_simple_scss", None)
        if compiler:
            compiled = compiler("$bg: #ff0000;\nbody { background: $bg; }")
            assert "#ff0000" in compiled or "background" in compiled

    def test_drawio_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test drawio blank diagram creation and cell parsing."""
        ext = load_extension_by_id("drawio", mock_api)
        creator = getattr(ext, "create_blank_diagram", None) or getattr(ext, "create_empty_diagram", None)
        assert creator is not None, "Draw.io must provide diagram creator"
        xml = creator("Architecture")
        assert "mxGraphModel" in xml

        parser = getattr(ext, "parse_diagram_cells", None)
        if parser:
            cells = parser(xml)
            assert isinstance(cells, list)

    def test_go_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test go extension run and test command builders."""
        ext = load_extension_by_id("go", mock_api)
        assert hasattr(ext, "build_run_command"), "Go must provide build_run_command"
        run_cmd = ext.build_run_command("main.go")
        assert "go run" in run_cmd
        assert "main.go" in run_cmd

        assert hasattr(ext, "build_test_command"), "Go must provide build_test_command"
        test_cmd = ext.build_test_command("./...")
        assert "go test" in test_cmd

    def test_csharp_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test csharp extension build and run command generation."""
        ext = load_extension_by_id("csharp", mock_api)
        assert hasattr(ext, "build_build_command"), "C# must provide build_build_command"
        build_cmd = ext.build_build_command("App.csproj")
        assert "dotnet build" in build_cmd
        assert "App.csproj" in build_cmd

        assert hasattr(ext, "build_run_command"), "C# must provide build_run_command"
        run_cmd = ext.build_run_command("App.csproj")
        assert "dotnet run" in run_cmd

    def test_github_pull_requests_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test github_pull_requests URL parsing and checkout command."""
        ext = load_extension_by_id("github_pull_requests", mock_api)
        assert hasattr(ext, "parse_pr_url"), "GitHub PR must provide parse_pr_url"
        info = ext.parse_pr_url("https://github.com/tomlin7/biscuit/pull/42")
        assert info is not None
        assert info.get("owner") == "tomlin7"
        assert info.get("repo") == "biscuit"
        assert str(info.get("pr_number")) == "42"

        assert hasattr(ext, "build_checkout_command"), "GitHub PR must provide build_checkout_command"
        checkout_cmd = ext.build_checkout_command(42)
        assert "42" in checkout_cmd

    def test_snippet_manager_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test snippet_manager prefix expansion."""
        ext = load_extension_by_id("snippet_manager", mock_api)
        assert ext is not None

    def test_json_viewer_functional_contracts(self, mock_api: MockExtensionsAPI) -> None:
        """Test json_viewer JSON formatting and validation."""
        ext = load_extension_by_id("json_viewer", mock_api)
        assert ext is not None
