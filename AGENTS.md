# Biscuit Extensions — Agent Guide

## Repo structure

```
extensions/          # each extension is a git submodule
extensions.toml      # marketplace manifest — keys match submodule folder names
.gitmodules          # submodule registry
```

Every submodule must be registered in **both** `.gitmodules` and `extensions.toml`.

## Adding a new extension

```bash
git submodule add https://github.com/biscuit-extensions/<name>.git extensions/<name>
git submodule update --init --remote
```

Then append to `extensions.toml`:

```toml
[<folder-name>]
submodule = "<folder-name>"
name = "<Display Name>"
author = "<author>"
description = "<short description>"
version = "<from pyproject.toml>"
```

The TOML key **must** match the submodule folder name (e.g. `[browser]` for `extensions/browser`). The `name` field is the display name.

Commit with:
```bash
git add extensions/<name> extensions.toml .gitmodules
git commit -m "Add <name> extension"
```

## Metadata source

Read the extension's `pyproject.toml` for the canonical `name`, `version`, `authors`, and `description`. Example:

```toml
# pyproject.toml
name = "browser"       # → submodule & TOML key
version = "0.1.0"      # → version
authors = ["biscuit"]  # → author
description = "..."    # → description
```

## Extension protocol

- Every extension is a Python Poetry project depending on `biscuit-editor`.
- Entrypoint: `src/<name>/__init__.py` exposing `setup(api)`.
- Test with `pytest` (no special runner needed).
- Dev mode: `biscuit ext dev` from the extension directory.

## Quirks

- `extensions/rose/` exists on disk but is **not** a git submodule and **not** registered in `extensions.toml`. Do not treat it as a model for new additions.
- All extension repos live under `github.com/biscuit-extensions/`.
- `biscuit ext publish` validates and prints instructions — it does not push. The actual process is: fork this repo → add submodule → update `extensions.toml` → open a PR.
