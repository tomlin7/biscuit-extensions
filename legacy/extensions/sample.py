# TEMPLATE FOR EXTENSION DEVELOPMENT

# Guide to Extension Development:
# 1. Create a new file in the `biscuit/extensions` folder
# 2. Name it something.py (e.g. hello_world.py)
# 3. Add following lines (for intellisense):

from __future__ import annotations

__version__ = "0.2.0"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import typing

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI

# 4. Create a class named `Extension` as follows:


class DevMode:
    """Dev Mode extension for Biscuit (author: @billyeatcookies)

    Contributes:
    - notifies user that dev mode is enabled
    """

    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.api.notifications.info(f"Dev mode is enabled!")

    def install(self): ...


def setup(api: ExtensionsAPI) -> None:
    """Setup the extension"""
    api.register("dev", DevMode(api))


# 5. Start customizing your extension!
