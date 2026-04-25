from __future__ import annotations

import typing

from .rose import Rose, RoseCanvas, RoseEditor

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


def setup(api: "ExtensionsAPI") -> None:
    api.register("rose", Rose(api))


__all__ = ["setup", "Rose", "RoseCanvas", "RoseEditor"]