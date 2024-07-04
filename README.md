<div align=center>
  <h1><a href=https://billyeatcookies.github.io/biscuit-extensions>BISCUIT EXTENSIONS REPOSITORY</a></h1>
</div><br>

The repository holds the extensions for the [**Biscuit Code Editor**](https://github.com/billyeatcookies/Biscuit) as well as the source code for extensions marketplace site. Read [extension API documentation](https://billyeatcookies.github.io/biscuit/) on the editor site for further information on writing and publishing extensions for Biscuit! [**_Visit the marketplace_**](https://billyeatcookies.github.io/biscuit-extensions) to see and review all of the available extensions.

## Writing Your First Extension

Use the following template for simplifying the process of writing extensions for Biscuit, this guide will get you started with the Extension API:

```py
# TEMPLATE FOR EXTENSION DEVELOPMENT

# Guide to Extension Development:
# 1. Clone the Biscuit repository
# 2. Create a new python file in the `biscuit/extensions` folder
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
    api.register("helloworld", HelloWorld(api))


# 5. Start customizing your extension!
```

Next:

- [Extension API documentation (🚧)](https://billyeatcookies.github.io/biscuit/)
- [Read API source code](https://github.com/billyeatcookies/biscuit/tree/main/biscuit/core/api)

## Publishing to Marketplace

You can contribute the awesome extensions you've made for Biscuit here, Follow these steps:

1. Add your extension's script to `extensions/` directory
2. Add your extension to `extensions.json` and the process is complete, follow the format below:

```json
"extension name": ["filename", "author name", "short description"]
```

> [!NOTE]
> Currently the extensions repository requires the extensions to be in a single source file.

## About

To contribute to the Biscuit project, visit the [Biscuit GitHub repository](https://github.com/billyeatcookies/Biscuit).
