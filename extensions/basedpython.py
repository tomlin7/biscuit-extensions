from __future__ import annotations

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import subprocess
import typing

from biscuit.extensions import Extension
from biscuit.language import Languages

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class BasedPython(Extension):
    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)

    def install(self) -> None:
        self.install_based_pyright()
        # overrides the default python language server with the based pyright language server
        self.api.register_langserver(
            Languages.PYTHON, "basedpyright-langserver --stdio"
        )

    def install_based_pyright(self, *_) -> bool:
        try:
            subprocess.run(["pip", "install", "basedpyright"], check=True)
        except Exception as e:
            self.api.notifications.error(
                f"Failed to install basedpyright package.",
                actions=[("Retry", self.install_based_pyright)],
            )


def setup(api: ExtensionsAPI) -> None:
    """Setup the extension"""
    api.register("basedpython", BasedPython(api))
