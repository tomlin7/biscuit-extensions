from __future__ import annotations

import threading

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import os
import subprocess as sp
import typing

try:
    import ruff
except ImportError:
    try:
        sp.run(["pip", "install", "ruff"], check=True)
        sp.run(["pip", "install", "python-lsp-ruff"], check=True)
        import ruff
    except Exception as e:
        ruff = None

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Ruff:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.base = api.base

    def install(self) -> None:
        if not ruff:
            return self.api.notifications.info(
                "ruff pip package is not installed. Install it to use this extension.",
                actions=[
                    (
                        "Install",
                        lambda: self.api.terminalmanager.run_command(
                            "pip install ruff python-lsp-ruff"
                        ),
                    ),
                ],
            )
        self.api.commands.register_command("Ruff: Format active editor", self.format)
        self.api.commands.register_command("Ruff: Check active file", self.check_file)
        self.api.commands.register_command(
            "Ruff: Check all files", self.check_all_files
        )

    def format(self, *_) -> str:
        editor = self.api.editorsmanager.active_editor
        if not (editor and editor.content and editor.content.editable):
            return

        text = editor.content.text
        if not text:
            return

        try:
            sp.check_output(["ruff", "format", editor.content.path])
            text.load_file()
        except sp.CalledProcessError as e:
            self.api.notifications.error(f"Ruff: Failed to format file")
            self.api.logger.error(e)
            return

    def check_file(self, *_):
        if not self.base.editorsmanager.active_editor:
            return

        path = os.path.abspath(self.base.editorsmanager.active_editor.path)
        try:
            output = sp.run(
                f"ruff check {path}",
                shell=True,
                capture_output=True,
                text=True,
            )
            self.base.problems.write(output.stdout)
        except sp.CalledProcessError as e:
            self.base.problems.clear()

    def check_all_files(self, *_):
        threading.Thread(target=self.threaded_check_all_files, daemon=True).start()

    def threaded_check_all_files(self):
        try:
            output = sp.run(
                f"ruff check {self.base.active_directory}",
                shell=True,
                capture_output=True,
                text=True,
            )
            self.base.problems.write(output.stdout)
        except sp.CalledProcessError as e:
            self.base.problems.clear()


def setup(api: ExtensionsAPI) -> Ruff:
    api.register("ruff", Ruff(api))
