"""Public API with deferred trading-agent imports."""

from importlib import import_module
from typing import TYPE_CHECKING

from autohedge.env_loader import load_env

if TYPE_CHECKING:
    from autohedge.main import AutoHedge

load_env()

__all__ = ["AutoHedge"]


def __getattr__(name):
    if name == "AutoHedge":
        return import_module("autohedge.main").AutoHedge
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
