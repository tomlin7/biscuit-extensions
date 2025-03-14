from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import subprocess as sp
import typing

try:
    import autopep8
except ImportError:
    try:
        sp.run(["pip", "install", "autopep8"], check=True)
        import autopep8
    except Exception as e:
        autopep8 = None

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Autopep8:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.base = api.base

    def install(self) -> None:
        if not autopep8:
            return self.api.notifications.info(
                "autopep8 pip package is not installed. Install it to use this extension.",
                actions=[
                    (
                        "Install",
                        lambda: self.api.terminalmanager.run_command(
                            "pip install autopep8"
                        ),
                    ),
                ],
            )
        self.api.commands.register_command(
            "Autopep8: Format active editor", self.format
        )

    def format(self, *_) -> str:
        import autopep8

        editor = self.api.editorsmanager.active_editor
        if not (editor and editor.content and editor.content.editable):
            return

        text = editor.content.text
        if not text:
            return

        before = text.get_all_text()
        try:
            formatted = autopep8.fix_code(before)
            if before != formatted:
                editor.content.text.load_text(formatted)

        except sp.CalledProcessError as e:
            self.api.notifications.error(f"Autopep8: Failed to format file, see logs.")
            self.api.logger.error(e)
            return


def setup(api: ExtensionsAPI) -> Autopep8:
    api.register("autopep8", Autopep8(api))
