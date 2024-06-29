<div align=center>
  <h1><a href=https://billyeatcookies.github.io/biscuit-extensions>BISCUIT EXTENSIONS REPOSITORY</a></h1>
</div><br>

The repository holds the extensions for the [**Biscuit Code Editor**](https://github.com/billyeatcookies/Biscuit) as well as the source code for extensions marketplace site. Read [extension API documentation](https://billyeatcookies.github.io/biscuit/) on the editor site for further information on writing and publishing extensions for Biscuit! [**_Visit the marketplace_**](https://billyeatcookies.github.io/biscuit-extensions) to see and review all of the available extensions.

## Getting Started

Use the following template for simplifying the process of writing extensions for Biscuit, this guide will get you started with the Extension API:

```py
# TEMPLATE FOR EXTENSION DEVELOPMENT

# STEPS:
# 1. Create a new file in the `biscuit/extensions` folder
# 2. Name it something.py (e.g. hello_world.py)
# 3. Add following lines (for intellisense):

from __future__ import annotations

__version__ = '0.2.0'
__version_info__ = tuple([ int(num) for num in __version__.split('.')])

import typing

if typing.TYPE_CHECKING:
    from biscuit import ExtensionsAPI

# 4. Create a class named `Extension` as follows:

class Extension:
    """Hello World extension for Biscuit (author: @ghost)

    Contributes:
    - notification "Hello world!"
    """

    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api


        self.api.notifications.info("Hello world!")

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
