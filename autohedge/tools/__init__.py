"""
Tool exports. Imports are lazy so an optional dependency (e.g. `solders`)
being absent never breaks `import autohedge`.
"""

from __future__ import annotations

import importlib
from typing import Any

_EXPORTS = {
    "get_ticker_overview": "autohedge.tools.polygon_api",
    "get_balance_sheets": "autohedge.tools.polygon_api",
    "get_daily_ticker_summary": "autohedge.tools.polygon_api",
    "search_tokens": "autohedge.tools.jupiter_search",
    "get_token_price": "autohedge.tools.jupiter_price",
    "execute_trade": "autohedge.tools.ultra_tools",
    "get_order": "autohedge.tools.ultra_tools",
    "get_holdings": "autohedge.tools.ultra_tools",
    "get_stock_quote": "autohedge.tools.yahoo_api",
    "get_historical_prices": "autohedge.tools.yahoo_api",
    "get_quote_summary": "autohedge.tools.yahoo_api",
    "get_all_stock_data": "autohedge.tools.yahoo_api",
    "exa_search": "autohedge.tools.exa_search_tool",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_path = _EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(module_path), name)
