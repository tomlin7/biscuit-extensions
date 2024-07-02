from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import threading
import time
import tkinter as tk
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class StatsOnBar:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.statusbar = self.api.statusbar
        self.sysinfo = self.api.sysinfo
        self.btn = self.statusbar.add_button(
            text=self.sysinfo.get_current_stats(),
            icon="pulse",
            description="CPU and Memory usage",
            side=tk.LEFT,
            padx=(2, 0),
        )

    def update_stats(self) -> None:
        while self.alive:
            time.sleep(1)
            self.btn.change_text(self.sysinfo.get_current_stats())

    def install(self) -> None:
        self.alive = True
        self.btn.show()
        threading.Thread(target=self.update_stats, daemon=True).start()

    def uninstall(self) -> None:
        self.alive = False
        self.btn.destroy()


def setup(api: ExtensionsAPI) -> StatsOnBar:
    api.register("statsonbar", StatsOnBar(api))
