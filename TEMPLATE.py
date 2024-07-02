# TEMPLATE FOR EXTENSION DEVELOPMENT

# Guide to Extension Development:
# 1. Create a new file in the `biscuit/extensions` folder
# 2. Name it something.py (e.g. hello_world.py)
# 3. Make sure you've installed `biscuit-editor` using `pip install biscuit-editor`

from __future__ import annotations

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import typing

from biscuit.extensions import Extension

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI

# 4. Create a class for your extension as follows:


class HelloWorld(Extension):
    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)

        self.api.logger.info(f"This is a sample log!")

    def install(self) -> None:
        self.api.notifications.info(f"Hello world!")


def setup(api: ExtensionsAPI) -> None:
    """Setup the extension"""
    api.register("dev", HelloWorld(api))


# 5. Start customizing your extension!
