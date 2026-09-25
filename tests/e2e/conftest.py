from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest

# Ensure repository root and biscuit core are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXTENSIONS_DIR = REPO_ROOT / "extensions"
BISCUIT_ROOT = REPO_ROOT.parent / "biscuit"
BISCUIT_SRC = BISCUIT_ROOT / "src"

if str(BISCUIT_SRC) not in sys.path and BISCUIT_SRC.exists():
    sys.path.insert(0, str(BISCUIT_SRC))

TOP_25_EXTENSIONS = [
    "docker",
    "python",
    "prettier",
    "eslint",
    "gitlens",
    "git_graph",
    "tailwind_css",
    "thunder_client",
    "live_server",
    "diff_viewer",
    "error_lens",
    "markdown_tools",
    "todo_tracker",
    "spell_checker",
    "bookmarks",
    "emmet_biscuit",
    "jupyter",
    "remote_ssh",
    "live_sass",
    "drawio",
    "go",
    "csharp",
    "github_pull_requests",
    "snippet_manager",
    "json_viewer",
]


class MockCommands:
    """Mock implementation of Biscuit Commands registry."""

    def __init__(self) -> None:
        self.commands: dict[str, Callable] = {}
        self.categories: dict[str, str] = {}

    def register_command(self, name: str, callback: Callable, category: str = "") -> None:
        self.commands[name] = callback
        self.categories[name] = category

    def execute_command(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name in self.commands:
            return self.commands[name](*args, **kwargs)
        raise KeyError(f"Command '{name}' not found")


class MockSettings:
    """Mock implementation of Biscuit Settings registry."""

    def __init__(self) -> None:
        self.registered_settings: dict[str, dict[str, Any]] = {}
        self.data: dict[str, Any] = {}

    def register_setting(
        self,
        name: str,
        type: str = "string",
        default: Any = None,
        description: str = "",
    ) -> None:
        self.registered_settings[name] = {
            "name": name,
            "type": type,
            "default": default,
            "description": description,
        }
        if name not in self.data and default is not None:
            self.data[name] = default

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_registered_settings(self) -> dict[str, dict[str, Any]]:
        return self.registered_settings.copy()


class MockStatusbarButton:
    """Mock implementation of SButton for Biscuit Statusbar."""

    def __init__(self, **kwargs: Any) -> None:
        self.text: str = kwargs.get("text", "")
        self.icon: str = kwargs.get("icon", "")
        self.callback: Callable | None = kwargs.get("callback")
        self.description: str = kwargs.get("description", "")
        self.side: Any = kwargs.get("side", None)
        self.padx: Any = kwargs.get("padx", None)
        self.visible: bool = False

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def change_text(self, text: str) -> None:
        self.text = text

    def change_icon(self, icon: str) -> None:
        self.icon = icon

    def change_description(self, desc: str) -> None:
        self.description = desc

    def click(self) -> Any:
        if self.callback:
            return self.callback()
        return None


class MockStatusbar:
    """Mock implementation of Biscuit Statusbar."""

    def __init__(self) -> None:
        self.buttons: list[MockStatusbarButton] = []

    def add_button(self, **kwargs: Any) -> MockStatusbarButton:
        btn = MockStatusbarButton(**kwargs)
        self.buttons.append(btn)
        return btn


class MockTextWidget:
    """In-memory simulated Tkinter Text widget for editor testing."""

    def __init__(self, initial_text: str = "") -> None:
        self._content: str = initial_text
        self.tags: dict[str, list[dict[str, Any]]] = {}
        self.tag_styles: dict[str, dict[str, Any]] = {}

    def get(self, start: str = "1.0", end: str = "end-1c") -> str:
        lines = self._content.splitlines(keepends=True)
        if not lines:
            return ""

        if start in ("1.0", "1.0-1c") and end in ("end", "end-1c"):
            return self._content

        try:
            start_parts = [int(p) for p in start.split(".")]
            s_line = max(1, start_parts[0]) - 1
            s_col = start_parts[1] if len(start_parts) > 1 else 0

            if end in ("end", "end-1c"):
                res = lines[s_line:]
                if not res:
                    return ""
                res[0] = res[0][s_col:]
                return "".join(res)

            end_parts = [int(p) for p in end.split(".")]
            e_line = max(1, end_parts[0]) - 1
            e_col = end_parts[1] if len(end_parts) > 1 else 0

            if s_line == e_line:
                if s_line < len(lines):
                    return lines[s_line][s_col:e_col]
                return ""

            selected = lines[s_line : e_line + 1]
            if selected:
                selected[0] = selected[0][s_col:]
                selected[-1] = selected[-1][:e_col]
            return "".join(selected)
        except Exception:
            return self._content

    def insert(self, index: str, text: str) -> None:
        if index in ("1.0", "0.0"):
            self._content = text + self._content
        elif index in ("end", "end-1c"):
            self._content += text
        else:
            self._content += text

    def delete(self, start: str = "1.0", end: str = "end") -> None:
        if start in ("1.0", "0.0") and end in ("end", "end-1c"):
            self._content = ""
        else:
            self._content = ""

    def tag_add(self, tag_name: str, start: str, end: str | None = None) -> None:
        if tag_name not in self.tags:
            self.tags[tag_name] = []
        self.tags[tag_name].append({"start": start, "end": end})

    def tag_config(self, tag_name: str, **kwargs: Any) -> None:
        if tag_name not in self.tag_styles:
            self.tag_styles[tag_name] = {}
        self.tag_styles[tag_name].update(kwargs)

    def tag_remove(self, tag_name: str, start: str, end: str | None = None) -> None:
        if tag_name in self.tags:
            self.tags[tag_name].clear()

    def tag_names(self) -> list[str]:
        return list(self.tags.keys())


class MockEditor:
    """Mock Biscuit Editor instance."""

    def __init__(self, path: str = "test.txt", content: str = "") -> None:
        self.path: str = path
        self.text: MockTextWidget = MockTextWidget(content)
        self.content: Any = type("Content", (), {"text": self.text})()


class MockEditors:
    """Mock Editors manager."""

    def __init__(self) -> None:
        self.active_editor: MockEditor | None = None
        self.opened_editors: list[MockEditor] = []
        self.opened_diff_editors: list[dict[str, Any]] = []

    def open_editor(self, path: str, exists: bool = True) -> MockEditor:
        ed = MockEditor(path=path)
        self.opened_editors.append(ed)
        self.active_editor = ed
        return ed

    def open_diff_editor(
        self,
        path: str,
        exists: bool = True,
        original: str = "",
        modified: str = "",
    ) -> dict[str, Any]:
        entry = {"path": path, "original": original, "modified": modified}
        self.opened_diff_editors.append(entry)
        return entry


class MockViews:
    """Mock Views manager."""

    def __init__(self) -> None:
        self.sidebar_views: list[Any] = []
        self.panel_views: list[Any] = []

    def add_sidebar_view(self, view: Any) -> None:
        self.sidebar_views.append(view)

    def add_panel_view(self, view: Any) -> None:
        self.panel_views.append(view)


class MockLogger:
    """Mock Logger recording all emitted logs."""

    def __init__(self) -> None:
        self.entries: list[tuple[str, str]] = []

    def info(self, msg: str) -> None:
        self.entries.append(("info", str(msg)))

    def warning(self, msg: str) -> None:
        self.entries.append(("warning", str(msg)))

    def error(self, msg: str) -> None:
        self.entries.append(("error", str(msg)))


class MockNotifications:
    """Mock Notifications recording toast alerts."""

    def __init__(self) -> None:
        self.toasts: list[tuple[str, str]] = []

    def info(self, msg: str) -> None:
        self.toasts.append(("info", str(msg)))

    def warning(self, msg: str) -> None:
        self.toasts.append(("warning", str(msg)))

    def error(self, msg: str) -> None:
        self.toasts.append(("error", str(msg)))


class MockTerminalManager:
    """Mock Terminal Manager."""

    def __init__(self) -> None:
        self.launched_terminals: list[dict[str, Any]] = []

    def open_terminal(self, command: str | None = None, title: str = "") -> dict[str, Any]:
        term = {"command": command, "title": title}
        self.launched_terminals.append(term)
        return term


class MockExtensionsAPI:
    """Headless Standalone ExtensionsAPI Mock."""

    def __init__(self) -> None:
        self.base: Any = MagicMock()
        self.commands: MockCommands = MockCommands()
        self.settings: MockSettings = MockSettings()
        self.statusbar: MockStatusbar = MockStatusbar()
        self.editors: MockEditors = MockEditors()
        self.views: MockViews = MockViews()
        self.logger: MockLogger = MockLogger()
        self.notifications: MockNotifications = MockNotifications()
        self.terminalmanager: MockTerminalManager = MockTerminalManager()

        self.registered_extensions: dict[str, Any] = {}
        self.comment_prefixes: dict[str, str] = {}
        self.langservers: dict[str, str] = {}
        self.run_commands: dict[str, str] = {}
        self.debuggers: dict[str, Any] = {}
        self.dap_adapters: dict[str, Any] = {}

    def register(self, name: str, extension: Any) -> None:
        self.registered_extensions[name] = extension
        if hasattr(extension, "install"):
            try:
                extension.install()
            except Exception:
                pass

    def register_extension(self, name: str, extension: Any) -> None:
        self.register(name, extension)

    def register_comment_prefix(self, language: str, prefix: str) -> None:
        self.comment_prefixes[language] = prefix

    def register_langserver(self, language: str, command: str) -> None:
        self.langservers[language] = command

    def register_run_command(self, language: str, command: str) -> None:
        self.run_commands[language] = command

    def register_debugger(self, language: str, debugger: Any) -> None:
        self.debuggers[language] = debugger

    def register_dap_adapter(self, language: str, adapter_command: Any) -> None:
        self.dap_adapters[language] = adapter_command


def load_extension_by_id(ext_id: str, api: MockExtensionsAPI) -> Any:
    """Dynamically loads and bootstraps an extension by ID from extensions/<ext_id>."""
    ext_dir = (EXTENSIONS_DIR / ext_id).resolve()
    if not ext_dir.is_dir():
        raise FileNotFoundError(f"Extension directory not found: {ext_dir}")

    # Ensure extension root is in sys.path
    ext_path_str = str(ext_dir)
    if ext_path_str not in sys.path:
        sys.path.insert(0, ext_path_str)

    init_file = ext_dir / "src" / ext_id / "__init__.py"
    if not init_file.exists():
        raise FileNotFoundError(f"Extension entrypoint not found: {init_file}")

    module_name = f"src.{ext_id}"
    spec = importlib.util.spec_from_file_location(module_name, init_file)
    if not spec or not spec.loader:
        raise ImportError(f"Could not create spec for {init_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if hasattr(module, "setup"):
        result = module.setup(api)
        if ext_id in api.registered_extensions:
            return api.registered_extensions[ext_id]
        if result is not None:
            return result

    return api.registered_extensions.get(ext_id)


@pytest.fixture
def mock_api() -> MockExtensionsAPI:
    """Fixture providing a clean headless MockExtensionsAPI."""
    return MockExtensionsAPI()


@pytest.fixture
def dep_manager(mock_api: MockExtensionsAPI) -> Any:
    """Fixture providing Biscuit DependencyManager."""
    from biscuit.extensions.dependencies import DependencyManager
    return DependencyManager(logger=mock_api.logger, notifications=mock_api.notifications)


@pytest.fixture
def all_25_extension_ids() -> list[str]:
    """Fixture returning the ordered list of the top 25 Biscuit extension IDs."""
    return list(TOP_25_EXTENSIONS)
