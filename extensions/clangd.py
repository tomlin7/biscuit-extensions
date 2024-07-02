from __future__ import annotations

import threading

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import subprocess
import typing
import zipfile
from pathlib import Path

import requests

from biscuit.extensions import Extension
from biscuit.language import Languages

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class Clangd(Extension):
    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)

        self.langservers_path = Path(self.api.base.extensionsdir) / "langservers"
        self.zip_path = self.langservers_path / "clangd.zip"
        self.clangd_path = self.langservers_path / "clangd_18.1.3"
        self.executable_path = self.clangd_path / "bin" / "clangd"
        if self.api.sysinfo.is_windows:
            self.executable_path = self.executable_path.with_suffix(".exe")

    def install(self) -> None:
        try:
            subprocess.check_call(["clangd", "--version"])
            self.api.register_langserver(Languages.CPP, "clangd")
            self.api.register_langserver(Languages.C, "clangd")
        except:
            if not self.clangd_path.exists():
                self.notification = self.api.notifications.info(
                    "Clangd executable not found in system PATH\n\nWould you like to install the Clangd binaries?",
                    actions=[
                        ("Install", self.start_fetching),
                    ],
                )

            self.api.register_langserver(Languages.CPP, str(self.executable_path))
            self.api.register_langserver(Languages.C, str(self.executable_path))

    def start_fetching(self, *_) -> None:
        threading.Thread(target=self.fetch_clangd, daemon=True).start()

    def fetch_clangd(self) -> None:
        self.notification.delete()
        self.langservers_path.mkdir(exist_ok=True)
        self.api.notifications.info(f"Downloading clangd binaries...")

        if self.api.sysinfo.is_windows:
            url = "https://github.com/clangd/clangd/releases/download/18.1.3/clangd-windows-18.1.3.zip"
        else:
            url = "https://github.com/clangd/clangd/releases/download/18.1.3/clangd-linux-18.1.3.zip"

        response = requests.get(url)

        with open(self.zip_path, "wb") as file:
            file.write(response.content)

        with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
            zip_ref.extractall(self.langservers_path)

        self.api.notifications.info(f"Clangd binaries installed successfully.")


def setup(api: ExtensionsAPI) -> None:
    """Setup the extension"""
    api.register("clangd", Clangd(api))
