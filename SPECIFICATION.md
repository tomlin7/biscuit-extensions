# Biscuit Extension Specification (v2.0)

This document defines the architecture, manifest format, dependency isolation, and contribution points for Biscuit extensions.

---

## 1. Extension Directory Layout

Each Biscuit extension repository must adhere to the following directory layout:

```
<extension_id>/
├── extension.toml         # Canonical extension manifest (required)
├── pyproject.toml         # Python packaging metadata (standard)
├── README.md              # Documentation and usage guide
├── icon.png               # Extension icon (PNG format, min 64x64)
├── requirements.txt       # Optional fallback for Python dependencies
├── src/
│   └── <extension_id>/
│       ├── __init__.py    # Entry point exposing setup(api: ExtensionsAPI)
│       └── ...            # Internal extension modules
├── tests/
│   └── test_<name>.py     # Pytest test suite
└── .deps/                 # Isolated runtime dependencies (git-ignored, auto-generated)
    └── .installed         # Dependency environment signature hash
```

---

## 2. Manifest Schema (`extension.toml`)

`extension.toml` is the primary declarative manifest for Biscuit extensions.

### Example Manifest

```toml
[extension]
id = "python"
name = "Python"
version = "0.2.0"
description = "Rich Python language intelligence, linting, formatting, and DAP debugging support"
author = "tomlin7"
icon = "icon.png"
repository = "https://github.com/biscuit-extensions/python"

[dependencies]
python = [
    "pygls>=1.3.0",
    "jedi>=0.19.0"
]
tools = [
    "python",
    "ruff"
]

[contributes]
languages = [
    { id = "python", extensions = [".py", ".pyi"], comment_prefix = "#" }
]
commands = [
    { id = "python.run_file", title = "Python: Run Current File" }
]
```

### Manifest Fields

#### `[extension]` Table
- `id` *(string, required)*: Unique identifier for the extension (slug format: `[a-z0-9_]+`). Matches folder name under `src/`.
- `name` *(string, required)*: Human-readable display name.
- `version` *(string, required)*: Semver version string (e.g. `0.2.0`).
- `description` *(string, required)*: Brief summary of features.
- `author` *(string, required)*: Extension author or organization.
- `icon` *(string, optional)*: Path to extension icon relative to repository root (defaults to `icon.png`).
- `repository` *(string, optional)*: Source repository URL.

#### `[dependencies]` Table
- `python` *(array of strings, optional)*: List of PyPI package specifications required by the extension (e.g. `["docker>=7.0.0", "pyyaml"]`).
- `tools` *(array of strings, optional)*: List of system executable names expected to exist on `PATH` (e.g. `["docker", "go", "node", "ruff"]`). Biscuit automatically validates these via `shutil.which` and alerts the user if missing.

#### `[contributes]` Table (Optional Declarations)
- `languages`: Language grammar and comment definitions.
- `commands`: Command palette contributions.
- `views`: Sidebar panels or secondary views.
- `settings`: Configuration schemas exposed in Settings view.

---

## 3. Dependency Isolation Model

Biscuit does not pollute the user's global Python environment or virtual environments with extension-specific packages.

### Isolated Storage
- All packages declared in `[dependencies].python` or `requirements.txt` are installed directly into `<extension_dir>/.deps/` using `--target`.
- Installation is prioritized via high-speed `uv pip install --target <ext_dir>/.deps <packages>` with fallback to `python -m pip install --target`.

### Caching and Fingerprint
- After installation, an environment hash is written to `<extension_dir>/.deps/.installed`.
- The hash incorporates the Python minor version and sorted package specifications. If unchanged, Biscuit skips re-installation on subsequent startups.

### Runtime Sys.Path Injection
- Before importing an extension's `setup(api)` entrypoint, Biscuit ensures dependencies are satisfied and prepends `<extension_dir>/.deps` to `sys.path`.
- When an extension is uninstalled, its `.deps` folder is safely removed and its path is evicted from `sys.path`.

---

## 4. CLI Developer Workflow

Manage and verify extension dependencies using the Biscuit CLI:

```bash
# Inspect dependencies of the current development extension
biscuit ext deps

# Install dependencies into .deps for the current extension
biscuit ext deps --install

# Inspect dependencies of an installed extension
biscuit ext deps <extension_name>

# Force re-installation of dependencies
biscuit ext deps <extension_name> --install --force

# Launch Biscuit with isolated dependencies loaded
biscuit ext dev

# Run test suite
biscuit ext test
```
