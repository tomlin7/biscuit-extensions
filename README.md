<div align="center">
  <h1>Biscuit Extensions Repository</h1>
  <p><a href="https://tomlin7.github.io/biscuit-extensions">Marketplace Website</a> • <a href="https://tomlin7.github.io/biscuit">Extension API Docs</a> • <a href="https://github.com/tomlin7/biscuit-extensions?tab=readme-ov-file#-creating-a-new-extension">Developer Guide</a></p>
  <img src="https://github.com/user-attachments/assets/c706bb26-0b37-4de9-90af-ffc39b18aea2" />
</div><br>

The **Biscuit Extensions Repository** aggregates community developed extensions for the [Biscuit Code Editor](https://github.com/tomlin7/Biscuit).  
Each extension lives in its own git submodule inside the `extensions/` folder and is automatically surfaced in the online marketplace.

If you are **looking for an extension** just use the editor's built-in marketplace or the `biscuit ext` CLI (see below).

### List available extensions

```bash
biscuit ext list            # every extension in the marketplace
biscuit ext list -i         # only the extensions you have installed
biscuit ext list -u <user>  # extensions by a specific author
```

### Install / Uninstall

```bash
biscuit ext install <name>
biscuit ext uninstall <name>
```

The commands above download or remove the extension **without** requiring a restart of Biscuit.

## ✨ Creating a New Extension

The easiest way to start is the official scaffold template hosted at [biscuit-extensions/extension](https://github.com/biscuit-extensions/extension). You can browse official templates and examples [here](https://github.com/biscuit-extensions).

```bash
# create a new project called "my_extension" in the current directory
biscuit ext new my_extension

# use an official template or your own git repo
biscuit ext new my_extension -t <template name or any git repo url>
```

During creation you will be asked for a description, author and initial version.  
The generated project follows the structure expected by Biscuit:

```
my_extension/
└── src/
    └── my_extension/
        ├── __init__.py   # entry-point, exposes setup(api)
        └── widget.py     # your extension logic
└── tests/                # pytest suite (optional but recommended)
└── pyproject.toml        # project metadata (Poetry)
└── README.md
```

A minimal example showing the editor API:

```python
from biscuit.extensions import Extension
from biscuit.api import ExtensionsAPI

class HelloWorld(Extension):
    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)
        api.logger.info("Hello World extension loaded")

    def install(self) -> None:
        self.api.notifications.info("👋 Hello Biscuit!")
```

## Running Development Server

```bash
cd my_extension
biscuit ext dev    # launches Biscuit and hot-loads the extension in dev-mode
```

Test-driven development:

```bash
pip install pytest
biscuit ext test       # run the entire pytest suite
```

## 🚀 Publishing to the Marketplace

Once your extension is ready:

```bash
biscuit ext publish    # guide & checklist for first-time publishing
```

The command validates your project, optionally runs the test-suite and prints
step-by-step instructions for adding your repository as a **git sub-module** and
updating `extensions.toml`.

For subsequent releases use:

```bash
biscuit ext update     # checklist for bumping the version / commit
```

## Contributing

1. Fork this repository and keep your branch in sync with `main`.
2. Follow the publish / update instructions printed by the CLI.
3. Open a Pull Request – the team will review and merge it.
