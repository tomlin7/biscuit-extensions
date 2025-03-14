from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import threading
import time
import tkinter as tk
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Clock:
    """Clock for Biscuit Taskbar (author: @billyeatcookies)

    Contributes:
    - adds a clock widget to Biscuit taskbar
    """

    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api

        class SClock(api.SButton):
            def __init__(clock, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                clock.hour_24_format = True
                threading.Thread(target=clock.update, daemon=True).start()

            def update(clock) -> None:
                while True:
                    time.sleep(1)
                    time_live = time.strftime(
                        "%H:%M:%S" if clock.hour_24_format else "%I:%M:%S"
                    )
                    clock.text_label.config(text=time_live)

            def use_24_hour_format(clock, flag: str) -> None:
                "Use 24 hour format for clock"

                clock.hour_24_format = flag

        self.clock = SClock(api.statusbar, text="H:M:S", description="Time")
        self.time_actionset = api.ActionSet(
            "Configure clock format",
            "time:",
            [
                ("12 hours", lambda e=None: self.clock.use_24_hour_format(False)),
                ("24 hours", lambda e=None: self.clock.use_24_hour_format(True)),
            ],
        )
        self.api.base.palette.register_actionset(lambda: self.time_actionset)
        self.clock.change_function(function=self.change_time_format)
        self.clock.set_pack_data(side=tk.RIGHT)
        self.clock.show()

    def change_time_format(self, *_) -> None:
        self.api.base.palette.show("time:")

    def install(self) -> None: ...


def setup(api: ExtensionsAPI) -> Clock:
    api.register("clock", Clock(api))
