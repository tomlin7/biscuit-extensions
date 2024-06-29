from __future__ import annotations

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])


import subprocess as sp
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Python:
    """Python extension for Biscuit (author: @billyeatcookies)

    Extension will automatically install python-lsp-server if not installed.

    Contributes:
    - language server configuration for Python (pylsp)
    """

    def __init__(self, api):
        self.api = api

    def run(self):
        reqs = sp.check_output(["pip", "freeze"])
        if not "python-lsp-server".encode() in reqs:
            try:
                sp.check_call(["pip", "install", "python-lsp-server"])
            except sp.CalledProcessError:
                self.api.notifications.warning(
                    "Python extension requires python-lsp-server to be installed"
                )
        self.api.register_langserver("Python", "pylsp")


def setup(api: ExtensionsAPI) -> Python:
    api.register("python", Python(api))
