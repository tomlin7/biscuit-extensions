from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import os
import subprocess as sp
import tkinter as tk
import typing

import biscuit

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class VSCode(biscuit.common.BaseGame):
    name = "VSCode"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from tkwebview2.tkwebview2 import WebView2, have_runtime, install_runtime

        if not have_runtime():
            install_runtime()

        view = WebView2(self, 500, 500, background="black")
        view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        view.load_url("https://vscode.dev")


class VSCodeExtension:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.base = api.base

        if os.name != "nt":
            self.base.notifications.error("VSCode extension works only in  Windows")
            return

        self.check_webview_installation()

    def check_webview_installation(self):
        reqs = sp.check_output(["pip", "freeze"])
        if not "webview2".encode() in reqs:
            try:
                sp.check_call(["pip", "install", "webview2"])
            except sp.CalledProcessError:
                self.api.notifications.warning(
                    "VSCode extension requires pypi/webview2 to be installed"
                )

    def install(self):
        self.api.register_game(VSCode)


def setup(api: ExtensionsAPI) -> None:
    api.register("vscode", VSCodeExtension(api))
