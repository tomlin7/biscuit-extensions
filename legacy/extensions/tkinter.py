from __future__ import annotations

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import os
import subprocess as sp
import tkinter as tk
import typing

from biscuit.common.icons import Icons
from biscuit.extensions import Extension

try:
    import watchdog
except ImportError:
    try:
        sp.run(["pip", "install", "watchdog"], check=True)
    except Exception as e:
        watchdog = None


from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class TkinterDevServer(PatternMatchingEventHandler):
    """Tkinter dev server"""

    def __init__(self, ext: Tkinter, observe_changes=True) -> None:
        self.ext = ext
        self.base = ext.base
        self.path = ""
        self.observe_changes = observe_changes

        super().__init__(patterns=["*.py"])

        self.observer = Observer()
        self.observer.start()

    def watch(self, path) -> None:
        self.path = path
        self.observer.unschedule_all()
        if path and self.observe_changes:
            self.observer.schedule(self, path, recursive=True)

            self.base.logger.info(f"Hot reload enabled ({path})")

    def stop_watch(self) -> None:
        self.observer.stop()

    def on_created(self, event) -> None:
        self.base.logger.trace(f"Created {os.path.abspath(event.src_path)}")
        self.ext.hot_reload()

    def on_deleted(self, event) -> None:
        self.base.logger.trace(f"Deleted {os.path.abspath(event.src_path)}")
        self.ext.hot_reload()

    def on_modified(self, event) -> None:
        self.base.logger.trace(f"Modified {os.path.abspath(event.src_path)}")
        self.ext.hot_reload()

    def on_moved(self, event):
        self.base.logger.trace(f"Modified {os.path.abspath(event.src_path)}")
        self.ext.hot_reload()


class Tkinter(Extension):
    """Experimental tkinter extension for Biscuit (author: @tomlin7)

    ==================!! EXPERIMENTAL !!=====================

    Contributes:
    ...
    """

    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)
        self.base = api.base

        self.p = None
        if watchdog:
            self.server = TkinterDevServer(self)

        # self.start_btn = None
        self.stop_btn = None
        self.restart_btn = None

    def install(self) -> None:
        if not watchdog:
            self.api.notifications.info(
                "watchdog pip package is not installed. Install it to use this extension.",
                actions=[
                    (
                        "Install",
                        lambda: self.api.terminalmanager.run_command(
                            "pip install watchdog"
                        ),
                    ),
                ],
            )

        self.api.notifications.info(f"Run Start server command to get started")
        self.api.commands.register_command(
            "Tkinter: Start dev server", self.start_server
        )

        # self.start_btn = self.base.statusbar.add_button(
        #     "Start server",
        #     Icons.PLAY_CIRCLE,
        #     self.start_server,
        #     "Start tkinter dev server",
        #     highlighted=True,
        #     side=tk.LEFT,
        # )

        self.stop_btn = self.base.statusbar.add_button(
            "Stop server",
            Icons.STOP_CIRCLE,
            self.stop_server,
            "Stop tkinter dev server",
            highlighted=True,
            side=tk.LEFT,
        )

        self.restart_btn = self.base.statusbar.add_button(
            "Hot reload",
            Icons.FLAME,
            self.hot_reload,
            "Hot reload tkinter app",
            highlighted=True,
            side=tk.LEFT,
        )

        # UI tweaks
        self.stop_btn.bg = "#f84b3c"
        self.stop_btn.on_leave()

        self.base.root.bind("<Destroy>", self.stop_server)

    def start_server(self, *_) -> None:
        e = self.base.editorsmanager.active_editor
        if not (
            e
            and e.content
            and e.content.editable
            and e.content.exists
            and e.content.text.language == "Python"
        ):
            self.api.notifications.info(
                f"Starting tkinter dev server requires source file of app open in editor"
            )
            return

        # if no folder open, watches entire directory the file is in
        self.path = self.base.active_directory or os.path.dirname(e.path)
        self.entrypoint = e.path

        self.base.commands.show_logs()
        self.base.logger.info("Starting tkinter dev server...")

        self.start_python_process(e.path)
        self.server.watch(self.base.active_directory)

        self.base.logger.info(f"🔰 Listening to changes <<{self.p.pid}>>")

        self.stop_btn.show()
        self.restart_btn.show()

    def stop_server(self, *_) -> None:
        self.base.logger.info(f"Stopping tkinter dev server...")
        self.p.kill()
        self.server.stop_watch()

        self.stop_btn.hide()
        self.restart_btn.hide()

    def hot_reload(self) -> None:
        self.p.kill()
        self.start_python_process(self.entrypoint)
        self.base.root.focus_force()
        self.base.logger.info(f"Tkinter Hot reloaded <<PID: {self.p.pid}>>")

    def start_python_process(self, path):
        self.p = sp.Popen(["python", path])


def setup(api: ExtensionsAPI) -> None:
    """Setup the extension"""
    api.register("tkinter", Tkinter(api))
