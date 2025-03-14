from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import subprocess as sp
import typing

try:
    import yapf
except ImportError:
    try:
        sp.run(["pip", "install", "yapf"], check=True)
        import yapf
    except Exception as e:
        yapf = None

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class YAPF:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.base = api.base

    def install(self) -> None:
        if not yapf:
            return self.api.notifications.info(
                "YAPF pip package is not installed. Install it to use this extension.",
                actions=[
                    (
                        "Install",
                        lambda: self.api.terminalmanager.run_command(
                            "pip install yapf"
                        ),
                    ),
                ],
            )
        self.api.commands.register_command("YAPF: Format active editor", self.format)

    def format(self, *_) -> str:
        from yapf.yapflib.yapf_api import FormatCode

        editor = self.api.editorsmanager.active_editor
        if not (editor and editor.content and editor.content.editable):
            return

        text = editor.content.text
        if not text:
            return

        before = text.get_all_text()
        try:
            formatted, changed = FormatCode(before)
            if changed:
                editor.content.text.load_text(formatted)

        except sp.CalledProcessError as e:
            self.api.notifications.error(f"YAPF: Failed to format file, see logs.")
            self.api.logger.error(e)
            return


def setup(api: ExtensionsAPI) -> YAPF:
    api.register("yapf", YAPF(api))
