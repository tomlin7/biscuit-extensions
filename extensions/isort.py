from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import subprocess as sp
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class ISort:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.base = api.base

    def install(self) -> None:
        self.check_isort_installation()
        self.api.commands.register_command(
            "Isort: Reorder imports in active editor ", self.format
        )

    def check_isort_installation(self):
        try:
            sp.check_call(["pip", "install", "isort"], stderr=sp.PIPE, stdout=sp.PIPE)
            sp.check_call(
                ["pip", "install", "python-lsp-isort"], stderr=sp.PIPE, stdout=sp.PIPE
            )
        except sp.CalledProcessError:
            self.api.notifications.warning(
                "Isort is not installed. Install it to use this extension.",
                actions=[
                    (
                        "Install",
                        lambda: self.api.terminalmanager.run_command(
                            "pip install isort python-lsp-isort"
                        ),
                    ),
                ],
            )

    def format(self, *_) -> str:
        editor = self.api.editorsmanager.active_editor
        if not (editor and editor.content and editor.content.editable):
            return

        text = editor.content.text
        if not text:
            return

        before = text.get_all_text()
        try:
            output = sp.check_output(["isort", "-"], input=before.encode(text.encoding))
            after = output.decode(text.encoding).replace("\r\n", "\n")
            if before != after:
                text.load_text(after)
        except sp.CalledProcessError as e:
            self.api.notifications.error(f"Isort: Failed to format file")
            self.api.logger.error(e)
            return


def setup(api: ExtensionsAPI) -> ISort:
    api.register("isort", ISort(api))
