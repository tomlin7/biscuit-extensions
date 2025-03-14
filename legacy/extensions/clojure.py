from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])


import subprocess as sp
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Clojure:
    """Clojure extension for Biscuit (author: @Cid0rz)

    Extension will automatically install clojure and clojure language server if not installed.

    Contributes:
    - language server configuration for clojure (clojure-lsp)
    """

    def __init__(self, api):
        self.api = api

    def install(self):
        try:
            sp.check_call(["java ", "--version"])
        except sp.CalledProcessError:
            self.api.notifications.warning(
                "Clojure extension requires java to be installed & in your PATH."
            )
        try:
            sp.check_call(["clojure-lsp"])
        except sp.CalledProcessError:
            pass
        self.api.register_langserver("Clojure", "clojure-lsp")


def setup(api: ExtensionsAPI) -> Clojure:
    api.register("clojure", Clojure(api))
