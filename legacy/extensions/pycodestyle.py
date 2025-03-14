from __future__ import annotations

import os
import threading

__version__ = "0.2.2"
__version_info__ = tuple([int(num) for num in __version__.split(".")])


import subprocess as sp
import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Pycodestyle:
    def __init__(self, api: ExtensionsAPI):
        self.api = api
        self.base = api.base
        self.problems = self.base.problems
        self.em = self.base.editorsmanager

    def install(self):
        reqs = sp.check_output(["pip", "freeze"])
        if not "pycodestyle".encode() in reqs:
            try:
                sp.check_call(["pip", "install", "pycodestyle"])
            except sp.CalledProcessError:
                self.api.notifications.warning(
                    "Extension requires pycodestyle to be installed."
                )

        self.api.commands.register_command(
            "python: check all files (pycodestyle)", self.check_all_files
        )
        self.api.commands.register_command(
            "python: check active file (pycodestyle)", self.check_file
        )

    def check_file(self, *_):
        if not self.em.active_editor:
            return self.check_all_files()

        path = os.path.abspath(self.em.active_editor.path)
        try:
            output = sp.run(
                f"pycodestyle --first {path}",
                shell=True,
                capture_output=True,
                text=True,
            )
            self.problems.write(output.stdout)
        except sp.CalledProcessError as e:
            self.problems.clear()

    def check_all_files(self, *_):
        if not self.base.active_directory:
            return

        threading.Thread(target=self.threaded_check_all_files, daemon=True).start()

    def threaded_check_all_files(self):
        try:
            output = sp.run(
                f"pycodestyle --first {self.base.active_directory}",
                shell=True,
                capture_output=True,
                text=True,
            )
            self.problems.write(output.stdout)
        except sp.CalledProcessError as e:
            self.problems.clear()


def setup(api: ExtensionsAPI) -> Pycodestyle:
    api.register("pycodestyle", Pycodestyle(api))
