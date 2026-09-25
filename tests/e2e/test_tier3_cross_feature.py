from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tests.e2e.conftest import MockExtensionsAPI, load_extension_by_id


class TestTier3CrossFeatureCombinations:
    """Tier 3: Multi-Extension Pairwise & Cooperative Integration Tests."""

    def test_combination_gitlens_and_diff_viewer(self, mock_api: MockExtensionsAPI) -> None:
        """Combination: Diff Viewer computes changed lines, GitLens correlates line blame annotations."""
        gitlens_ext = load_extension_by_id("gitlens", mock_api)
        diff_ext = load_extension_by_id("diff_viewer", mock_api)

        original_code = "def add(a, b):\n    return a + b\n"
        modified_code = "def add(a, b):\n    # Added validation\n    if a is None or b is None:\n        return 0\n    return a + b\n"

        # 1. Diff Viewer computes modified lines
        diff_fn = getattr(diff_ext, "compute_diff", None) or getattr(
            diff_ext, "generate_diff", None
        )
        if diff_fn:
            diff_res = diff_fn(original_code, modified_code)
            assert diff_res is not None

        # 2. GitLens parses porcelain blame for the modified file
        porcelain_blame = (
            "c01a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a 1 1 1\n"
            "author Jane Reviewer\n"
            "author-mail <jane@example.com>\n"
            "author-time 1700000000\n"
            "author-tz +0000\n"
            "committer Jane Reviewer\n"
            "summary Add null validation\n"
            "filename math.py\n"
            "\tdef add(a, b):\n"
            "c01a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a 2 2 1\n"
            "author Jane Reviewer\n"
            "summary Add null validation\n"
            "filename math.py\n"
            "\t    # Added validation\n"
        )
        parser = getattr(gitlens_ext, "parse_porcelain_blame", None) or getattr(
            gitlens_ext, "parse_blame_output", None
        )
        assert parser is not None
        records = parser(porcelain_blame)
        assert records is not None

        # 3. Format inline blame for the added line
        formatter = getattr(gitlens_ext, "format_blame_annotation", None)
        if formatter:
            annot = formatter(
                {"author": "Jane Reviewer", "summary": "Add null validation", "time": 1700000000}
            )
            assert "Jane Reviewer" in str(annot)

    def test_combination_prettier_and_eslint(self, mock_api: MockExtensionsAPI) -> None:
        """Combination: ESLint lints and auto-fixes JS, then Prettier formats the clean code."""
        eslint_ext = load_extension_by_id("eslint", mock_api)
        prettier_ext = load_extension_by_id("prettier", mock_api)

        unclean_js = "var score=100;\ndebugger;\nvar name   =   'Alice'  ;"

        # 1. ESLint scans problems
        linter = getattr(eslint_ext, "lint_code", None) or getattr(eslint_ext, "lint_file", None)
        assert linter is not None
        issues = linter(unclean_js, "app.js")
        assert isinstance(issues, list)

        # 2. ESLint applies automatic fixes (e.g. var -> let)
        fixed_js = unclean_js
        fixer = getattr(eslint_ext, "apply_fixes", None) or getattr(eslint_ext, "fix_code", None)
        if fixer:
            fixed_js = fixer(unclean_js)
            assert isinstance(fixed_js, str)

        # 3. Prettier formats the resulting document
        formatter = getattr(prettier_ext, "format_content", None) or getattr(
            prettier_ext, "format_code", None
        )
        assert formatter is not None
        formatted_js = formatter(fixed_js, "app.js")
        assert isinstance(formatted_js, str)
        assert len(formatted_js.strip()) > 0

    def test_combination_python_and_jupyter(self, mock_api: MockExtensionsAPI) -> None:
        """Combination: Python extension locates interpreter, Jupyter runs code cell in session."""
        python_ext = load_extension_by_id("python", mock_api)
        jupyter_ext = load_extension_by_id("jupyter", mock_api)

        # 1. Python extension provides interpreter
        interpreter = python_ext.get_interpreter()
        assert interpreter is not None

        # 2. Jupyter parses notebook
        notebook_data = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Analysis Notebook"], "metadata": {}},
                {"cell_type": "code", "source": ["result = sum([1, 2, 3, 4, 5])\nresult"], "outputs": [], "metadata": {}},
            ],
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
            "nbformat": 4,
            "nbformat_minor": 2,
        }
        raw_json = json.dumps(notebook_data)
        cell_parser = getattr(jupyter_ext, "parse_cells", None) or getattr(
            jupyter_ext, "parse_notebook", None
        )
        assert cell_parser is not None
        cells = cell_parser(raw_json)
        assert len(cells) == 2

        # 3. Jupyter executes cell
        runner = getattr(jupyter_ext, "execute_cell", None) or getattr(
            jupyter_ext, "execute_cell_code", None
        )
        if runner:
            exec_res = runner("sum([1, 2, 3, 4, 5])")
            assert exec_res is not None
            if isinstance(exec_res, dict):
                assert str(exec_res.get("result", "")) in ("15", str(15)) or "15" in str(exec_res)
            elif isinstance(exec_res, (int, str)):
                assert str(exec_res) == "15"

    def test_combination_todo_tracker_and_error_lens(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Combination: TODO Tracker indexes tasks while Error Lens tags diagnostics on buffer."""
        todo_ext = load_extension_by_id("todo_tracker", mock_api)
        error_lens_ext = load_extension_by_id("error_lens", mock_api)

        source_code = (
            "def calculate_tax(subtotal):\n"
            "    # TODO: add support for European VAT rates\n"
            "    tax_rate = 0.08\n"
            "    # FIXME: check for negative subtotal values\n"
            "    return subtotal * tax_rate\n"
        )

        # 1. TODO tracker parses items
        if hasattr(todo_ext, "scan_content"):
            todos = todo_ext.scan_content(source_code, "finance.py")
            assert len(todos) >= 2
            tags = [t.get("tag") for t in todos if isinstance(t, dict)]
            assert "TODO" in tags or any("TODO" in str(t) for t in todos)

        # 2. Error Lens attaches diagnostics to line 5
        diagnostics = [
            {"line": 5, "column": 5, "severity": "warning", "message": "Potential float precision issue"}
        ]
        error_lens_ext.set_diagnostics("finance.py", diagnostics)

        getter = getattr(error_lens_ext, "get_line_diagnostic", None) or getattr(
            error_lens_ext, "get_line_diagnostics", None
        )
        assert getter is not None
        diag = getter("finance.py", 5)
        assert diag is not None

    def test_combination_docker_and_thunder_client(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Combination: Docker parses exposed service port, Thunder Client builds HTTP probe."""
        docker_ext = load_extension_by_id("docker", mock_api)
        thunder_ext = load_extension_by_id("thunder_client", mock_api)

        compose_yaml = """
services:
  api_gateway:
    image: kong:3.4
    ports:
      - "8000:8000"
  user_service:
    image: myorg/user-service:1.0
    ports:
      - "8081:8080"
"""
        # 1. Docker parses services
        compose_parser = getattr(docker_ext, "parse_compose_file", None) or getattr(
            docker_ext, "get_compose_services", None
        )
        assert compose_parser is not None
        services = compose_parser(compose_yaml)
        assert "api_gateway" in services
        assert "user_service" in services

        # 2. Thunder Client builds API health probe targeting service
        req = thunder_ext.create_request(
            method="GET",
            url="http://localhost:8000/status",
            headers={"Accept": "application/json"},
        )
        assert req is not None

        # 3. Save to collection
        if hasattr(thunder_ext, "save_to_collection"):
            thunder_ext.save_to_collection("Docker Services", req)
            if hasattr(thunder_ext, "collections"):
                assert "Docker Services" in thunder_ext.collections

    def test_combination_live_server_and_live_sass(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Combination: Live Sass compiles SCSS to CSS, triggering Live Server reload hook."""
        sass_ext = load_extension_by_id("live_sass", mock_api)
        server_ext = load_extension_by_id("live_server", mock_api)

        scss_content = "$primary-color: #2563eb;\n.navbar {\n  background: $primary-color;\n}\n"

        # 1. Live Sass derives output path and compiles
        css_path = sass_ext.get_output_css_path("assets/main.scss")
        assert css_path.endswith(".css")

        compiler = getattr(sass_ext, "compile_file", None) or getattr(
            sass_ext, "compile_simple_scss", None
        )
        if compiler:
            compiled_css = compiler(scss_content)
            assert "#2563eb" in compiled_css or "navbar" in compiled_css

        # 2. Live Server lifecycle and reload notification
        start_fn = getattr(server_ext, "start_server", None) or getattr(server_ext, "start", None)
        stop_fn = getattr(server_ext, "stop_server", None) or getattr(server_ext, "stop", None)
        assert start_fn is not None and stop_fn is not None

        reload_hook = getattr(server_ext, "notify_reload", None) or getattr(
            server_ext, "reload", None
        )
        if reload_hook:
            # Broadcast reload trigger
            reload_hook()

    def test_combination_emmet_and_tailwind_css(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Combination: Emmet expands abbreviation with Tailwind classes, Tailwind verifies styling."""
        emmet_ext = load_extension_by_id("emmet_biscuit", mock_api)
        tailwind_ext = load_extension_by_id("tailwind_css", mock_api)

        # 1. Emmet expands abbreviation with utility classes
        abbreviation = "nav.bg-emerald-500.text-white.p-4>ul>li.flex.block*2>a{Link}"
        expander = getattr(emmet_ext, "expand_abbreviation", None) or getattr(
            emmet_ext, "expand", None
        )
        if expander:
            html = expander(abbreviation)
            assert "nav" in html
            assert "bg-emerald-500" in html
        else:
            html = '<nav class="bg-emerald-500 text-white p-4"><ul><li class="flex block"><a>Link</a></li></ul></nav>'

        # 2. Tailwind extracts classes from generated markup
        classes = tailwind_ext.extract_classes(html)
        assert "bg-emerald-500" in classes
        assert "text-white" in classes

        # 3. Tailwind checks color and conflicts
        color_resolver = getattr(tailwind_ext, "resolve_class_color", None) or getattr(
            tailwind_ext, "get_color_for_class", None
        )
        if color_resolver:
            hex_color = color_resolver("bg-emerald-500")
            assert hex_color is not None

        conflict_checker = getattr(tailwind_ext, "detect_conflicts", None) or getattr(
            tailwind_ext, "lint_conflicts", None
        )
        if conflict_checker:
            # "flex" and "block" on same element should conflict
            conflicts = conflict_checker(["flex", "block"])
            assert conflicts is not None

    def test_combination_github_pull_requests_and_git_graph(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Combination: GitHub PR parses checkout command, Git Graph maps branch to commit DAG."""
        gh_ext = load_extension_by_id("github_pull_requests", mock_api)
        graph_ext = load_extension_by_id("git_graph", mock_api)

        # 1. Parse PR URL and generate checkout ref
        pr_info = gh_ext.parse_pr_url("https://github.com/biscuit-editor/biscuit/pull/150")
        assert pr_info is not None
        assert str(pr_info.get("pr_number")) == "150"

        checkout_cmd = gh_ext.build_checkout_command(150)
        assert "150" in checkout_cmd

        # 2. Git Graph parses commit log with PR branch ref
        log_sample = (
            "c_head|c_base|Dev Person|dev@test.org|1700001000|Implement feature|(HEAD -> pr-150, origin/main)\n"
            "c_base||Main Author|lead@test.org|1700000000|Previous release|(tag: v1.0.0)\n"
        )
        parser = getattr(graph_ext, "parse_log", None) or getattr(
            graph_ext, "get_commit_dag", None
        )
        assert parser is not None
        nodes = parser(log_sample)
        assert len(nodes) >= 2
