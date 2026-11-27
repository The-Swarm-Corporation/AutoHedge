"""
Tool exports. Imports are lazy so an optional dependency (e.g. `solders`)
being absent never breaks `import market_mind_ai`.
"""

from __future__ import annotations

import importlib
from typing import Any

_EXPORTS = {
    "get_ticker_overview": "market_mind_ai.tools.polygon_api",
    "get_balance_sheets": "market_mind_ai.tools.polygon_api",
    "get_daily_ticker_summary": "market_mind_ai.tools.polygon_api",
    "search_tokens": "market_mind_ai.tools.jupiter_search",
    "get_token_price": "market_mind_ai.tools.jupiter_price",
    "execute_trade": "market_mind_ai.tools.ultra_tools",
    "get_order": "market_mind_ai.tools.ultra_tools",
    "get_holdings": "market_mind_ai.tools.ultra_tools",
    "get_stock_quote": "market_mind_ai.tools.yahoo_api",
    "get_historical_prices": "market_mind_ai.tools.yahoo_api",
    "get_quote_summary": "market_mind_ai.tools.yahoo_api",
    "get_all_stock_data": "market_mind_ai.tools.yahoo_api",
    "exa_search": "market_mind_ai.tools.exa_search_tool",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_path = _EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(module_path), name)
