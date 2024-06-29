from __future__ import annotations

import time

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import threading
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class StatsOnBar:
    """System stats for Biscuit statusbar (author: @billyeatcookies)

    Contributes:
    - adds sysinfo to the statusbar
    """

    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.statusbar = self.api.statusbar
        self.sysinfo = self.api.sysinfo
        self.btn = self.statusbar.add_button(
            text=self.sysinfo.get_current_stats(),
            icon="pulse",
            description="CPU and Memory usage",
        )
        threading.Thread(target=self.update_stats, daemon=True).start()

    def update_stats(self) -> None:
        while True:
            time.sleep(1)
            self.btn.change_text(self.sysinfo.get_current_stats())

    def run(self) -> None: ...


def setup(api: ExtensionsAPI) -> StatsOnBar:
    api.register("statsonbar", StatsOnBar(api))
