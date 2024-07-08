from __future__ import annotations

__version__ = "0.3.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import subprocess as sp
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Black:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.base = api.base

        if "yapf" in self.base.extensions_manager.installed:
            self.api.notifications.warning(
                "Black will disable YAPF language server integration"
            )

        if "autopep8" in self.base.extensions_manager.installed:
            self.api.notifications.warning(
                "Black will disable Autopep8 language server integration"
            )

    def install(self) -> None:
        self.check_black_installation()
        self.api.commands.register_command(
            "Black Formatter: Format active editor", self.format
        )

    def check_black_installation(self):
        try:
            sp.check_call(["pip", "install", "black"])
            sp.check_call(["pip", "install", "python-lsp-black"])
        except sp.CalledProcessError:
            self.api.notifications.warning(
                "Black is not installed. Install it to use this extension.",
                actions=[
                    (
                        "Install",
                        lambda: self.api.terminalmanager.run_command(
                            "pip install black python-lsp-black"
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
            output = sp.check_output(["black", "-"], input=before.encode(text.encoding))
            after = output.decode(text.encoding)
            if before != after:
                text.load_text(after)
        except sp.CalledProcessError as e:
            self.api.notifications.error(f"Black: Failed to format file")
            self.api.logger.error(e)
            return


def setup(api: ExtensionsAPI) -> Black:
    api.register("black", Black(api))
