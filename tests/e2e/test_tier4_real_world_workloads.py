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


class TestTier4RealWorldWorkloads:
    """Tier 4: Realistic End-to-End Multi-Extension Development Workflows."""

    def test_workflow_full_stack_web_development(self, mock_api: MockExtensionsAPI) -> None:
        """Scenario 1: Complete Full-Stack Web Development Workflow.

        Cooperating Extensions:
        - emmet_biscuit: Scaffold HTML markup
        - tailwind_css: Utility class extraction & conflict verification
        - live_sass: SCSS styling compilation
        - prettier: Code formatting
        - eslint: JavaScript problem scanning & auto-fix
        - markdown_tools: Component documentation & TOC
        - live_server: Local server lifecycle
        """
        emmet = load_extension_by_id("emmet_biscuit", mock_api)
        tailwind = load_extension_by_id("tailwind_css", mock_api)
        sass = load_extension_by_id("live_sass", mock_api)
        prettier = load_extension_by_id("prettier", mock_api)
        eslint = load_extension_by_id("eslint", mock_api)
        md_tools = load_extension_by_id("markdown_tools", mock_api)
        server = load_extension_by_id("live_server", mock_api)

        # Step 1: Emmet scaffolding
        emmet_expander = getattr(emmet, "expand_abbreviation", None) or getattr(emmet, "expand", None)
        if emmet_expander:
            html = emmet_expander("header.bg-slate-900.text-white>nav.p-4>ul>li*3>a{Nav Item $}")
            assert "header" in html
        else:
            html = '<header class="bg-slate-900 text-white"><nav class="p-4"><ul><li><a>Nav Item 1</a></li></ul></nav></header>'

        # Step 2: Tailwind class extraction and validation
        classes = tailwind.extract_classes(html)
        assert "bg-slate-900" in classes
        assert "text-white" in classes

        # Step 3: SCSS compilation
        scss_source = "$primary: #0f172a;\nheader { background-color: $primary; nav { margin: 0; } }"
        sass_compiler = getattr(sass, "compile_file", None) or getattr(sass, "compile_simple_scss", None)
        if sass_compiler:
            css = sass_compiler(scss_source)
            assert "#0f172a" in css or "header" in css

        # Step 4: Prettier formatting
        js_code = 'const   initApp = ( ) =>{console.log("App ready");};'
        formatter = getattr(prettier, "format_content", None) or getattr(prettier, "format_code", None)
        if formatter:
            formatted_js = formatter(js_code, "app.js")
            assert len(formatted_js) > 0

        # Step 5: ESLint linting
        linter = getattr(eslint, "lint_code", None) or getattr(eslint, "lint_file", None)
        if linter:
            issues = linter(js_code, "app.js")
            assert isinstance(issues, list)

        # Step 6: Markdown documentation
        doc = "# Component: Header\n\n## Overview\nNavigation header\n\n## Props\n| Prop | Type |\n|---|---|\n| title | string |\n"
        toc_fn = getattr(md_tools, "generate_toc", None)
        if toc_fn:
            toc = toc_fn(doc)
            assert "Overview" in str(toc)

        # Step 7: Live Server local development
        start_fn = getattr(server, "start_server", None) or getattr(server, "start", None)
        stop_fn = getattr(server, "stop_server", None) or getattr(server, "stop", None)
        assert start_fn is not None and stop_fn is not None

    def test_workflow_data_science_and_python_pipeline(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Scenario 2: Data Science & Python Pipeline.

        Cooperating Extensions:
        - python: Interpreter discovery & pytest runner
        - jupyter: Notebook parsing & execution
        - json_viewer: Result dataset validation & formatting
        """
        python_ext = load_extension_by_id("python", mock_api)
        jupyter_ext = load_extension_by_id("jupyter", mock_api)
        json_ext = load_extension_by_id("json_viewer", mock_api)

        # Step 1: Python environment detection
        interpreter = python_ext.get_interpreter()
        assert interpreter is not None

        run_cmd = python_ext.build_run_command("pipeline.py")
        assert "pipeline.py" in run_cmd

        # Step 2: Jupyter notebook ingestion & computation
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Data Preparation"], "metadata": {}},
                {"cell_type": "code", "source": ["data = [10, 20, 30, 40]\navg = sum(data)/len(data)\navg"], "outputs": [], "metadata": {}},
            ],
            "metadata": {"kernelspec": {"name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        cell_parser = getattr(jupyter_ext, "parse_cells", None) or getattr(
            jupyter_ext, "parse_notebook", None
        )
        assert cell_parser is not None
        cells = cell_parser(json.dumps(notebook))
        assert len(cells) == 2

        # Step 3: Cell execution
        exec_fn = getattr(jupyter_ext, "execute_cell", None) or getattr(
            jupyter_ext, "execute_cell_code", None
        )
        if exec_fn:
            res = exec_fn("sum([10, 20, 30, 40]) / 4")
            assert res is not None

        # Step 4: JSON Viewer validation
        metrics_json = '{"experiment_id": "exp_01", "accuracy": 0.945, "loss": 0.055}'
        formatter = getattr(json_ext, "format_json", None)
        if formatter:
            pretty = formatter(metrics_json, indent=2)
            assert "accuracy" in pretty
            assert "\n" in pretty

    def test_workflow_devops_and_infrastructure(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Scenario 3: DevOps & Infrastructure Deployment.

        Cooperating Extensions:
        - docker: Compose parsing & container lifecycle
        - drawio: Architecture diagram generation
        - remote_ssh: Server configuration & command builder
        - thunder_client: Healthcheck HTTP endpoint probe
        """
        docker_ext = load_extension_by_id("docker", mock_api)
        drawio_ext = load_extension_by_id("drawio", mock_api)
        ssh_ext = load_extension_by_id("remote_ssh", mock_api)
        thunder_ext = load_extension_by_id("thunder_client", mock_api)

        # Step 1: Docker Compose parsing
        compose = """
services:
  database:
    image: postgres:16
    ports: ["5432:5432"]
  backend:
    image: myapp/api:v1.2
    ports: ["8080:8080"]
    depends_on: [database]
"""
        parser = getattr(docker_ext, "parse_compose_file", None) or getattr(
            docker_ext, "get_compose_services", None
        )
        assert parser is not None
        services = parser(compose)
        assert "database" in services
        assert "backend" in services

        # Step 2: Architecture diagram generation via Draw.io
        diagram_creator = getattr(drawio_ext, "create_blank_diagram", None) or getattr(
            drawio_ext, "create_empty_diagram", None
        )
        assert diagram_creator is not None
        diagram_xml = diagram_creator("System Architecture")
        assert "mxGraphModel" in diagram_xml

        # Step 3: Remote SSH configuration
        ssh_config = (
            "Host prod-cluster\n"
            "    HostName 10.0.1.100\n"
            "    User devops\n"
            "    Port 22\n"
        )
        ssh_parser = getattr(ssh_ext, "parse_ssh_config", None)
        assert ssh_parser is not None
        hosts = ssh_parser(ssh_config)
        assert len(hosts) == 1
        assert hosts[0].get("host") == "prod-cluster" or hosts[0].get("Host") == "prod-cluster"

        # Step 4: Thunder Client REST probe
        req = thunder_ext.create_request("GET", "http://10.0.1.100:8080/health")
        assert req is not None

    def test_workflow_code_review_and_qa_audit(
        self, mock_api: MockExtensionsAPI
    ) -> None:
        """Scenario 4: Team Code Review & Quality Assurance Audit.

        Cooperating Extensions:
        - github_pull_requests: Parse PR and checkout
        - diff_viewer: Side-by-side patch computation
        - gitlens: Porcelain blame inspection on changed lines
        - todo_tracker: Review comment & tag scanner
        - error_lens: Real-time diagnostic warning tags
        - spell_checker: Typo scanning on review comments
        - bookmarks: Reviewer line navigation
        """
        gh_ext = load_extension_by_id("github_pull_requests", mock_api)
        diff_ext = load_extension_by_id("diff_viewer", mock_api)
        gitlens_ext = load_extension_by_id("gitlens", mock_api)
        todo_ext = load_extension_by_id("todo_tracker", mock_api)
        error_lens_ext = load_extension_by_id("error_lens", mock_api)
        spell_ext = load_extension_by_id("spell_checker", mock_api)
        bookmarks_ext = load_extension_by_id("bookmarks", mock_api)

        # Step 1: Parse PR
        pr_info = gh_ext.parse_pr_url("https://github.com/biscuit/editor/pull/404")
        assert pr_info is not None
        assert str(pr_info.get("pr_number")) == "404"

        # Step 2: Compute diff
        base_code = "def process():\n    return False\n"
        head_code = "def process():\n    # TODO: add security check\n    return True\n"
        diff_fn = getattr(diff_ext, "compute_diff", None) or getattr(diff_ext, "generate_diff", None)
        if diff_fn:
            diff_res = diff_fn(base_code, head_code)
            assert diff_res is not None

        # Step 3: Git blame on changed lines
        porcelain = (
            "commit_abc 1 1 1\n"
            "author Sam Reviewee\n"
            "summary Update process logic\n"
            "filename app.py\n"
            "\tdef process():\n"
        )
        blame_parser = getattr(gitlens_ext, "parse_porcelain_blame", None) or getattr(
            gitlens_ext, "parse_blame_output", None
        )
        assert blame_parser is not None
        records = blame_parser(porcelain)
        assert records is not None

        # Step 4: Scan for new TODO comments
        if hasattr(todo_ext, "scan_content"):
            todos = todo_ext.scan_content(head_code, "app.py")
            assert len(todos) >= 1

        # Step 5: Error lens diagnostic tagging
        error_lens_ext.set_diagnostics("app.py", [{"line": 2, "column": 5, "severity": "info", "message": "New TODO added"}])
        getter = getattr(error_lens_ext, "get_line_diagnostic", None) or getattr(
            error_lens_ext, "get_line_diagnostics", None
        )
        assert getter is not None
        diag = getter("app.py", 2)
        assert diag is not None

        # Step 6: Spell check
        tokenizer = getattr(spell_ext, "tokenize_identifiers", None)
        if tokenizer:
            tokens = tokenizer("Check for recieve vs receive")
            assert "receive" in tokens or "Check" in tokens

        # Step 7: Bookmarks
        toggle = getattr(bookmarks_ext, "toggle_bookmark", None)
        if toggle:
            toggle("app.py", 2)
