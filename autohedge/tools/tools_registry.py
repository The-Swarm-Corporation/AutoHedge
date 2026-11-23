"""
Lazy, fault-tolerant tool registry.

Tools are imported on demand so a missing optional dependency (for example
`solders` for live trading) never breaks `import autohedge` or the research
pipeline. Registry groups are wired into the corresponding agents in
`autohedge.workers`.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Callable, List

logger = logging.getLogger(__name__)

Tool = Callable[..., Any]


def _load(module_path: str, name: str, bucket: List[Tool]) -> None:
    """Append a tool to `bucket`, skipping it if its dependency is missing."""
    try:
        module = importlib.import_module(module_path)
        bucket.append(getattr(module, name))
    except Exception as exc:
        logger.warning("Tool %s.%s unavailable: %s", module_path, name, exc)


def get_research_tools() -> List[Tool]:
    """Web/news research tools for the sentiment agent."""
    tools: List[Tool] = []
    _load("autohedge.tools.exa_search_tool", "exa_search", tools)
    return tools


def get_market_data_tools() -> List[Tool]:
    """Price/fundamentals tools for the quant and risk agents."""
    tools: List[Tool] = []
    for name in (
        "get_stock_quote",
        "get_historical_prices",
        "get_quote_summary",
        "get_all_stock_data",
    ):
        _load("autohedge.tools.yahoo_api", name, tools)
    for name in (
        "get_ticker_overview",
        "get_balance_sheets",
        "get_daily_ticker_summary",
    ):
        _load("autohedge.tools.polygon_api", name, tools)
    for name in ("search_tokens",):
        _load("autohedge.tools.jupiter_search", name, tools)
    _load("autohedge.tools.jupiter_price", "get_token_price", tools)
    return tools


def get_execution_tools() -> List[Tool]:
    """Solana/Jupiter order and execution tools for the execution agent."""
    tools: List[Tool] = []
    for name in ("get_order", "execute_trade", "get_holdings"):
        _load("autohedge.tools.ultra_tools", name, tools)
    return tools


def get_tools() -> List[Tool]:
    """All available tools (backwards-compatible aggregate helper)."""
    tools: List[Tool] = []
    tools.extend(get_research_tools())
    tools.extend(get_market_data_tools())
    tools.extend(get_execution_tools())
    return tools


def load_tool(module_path: str, name: str) -> Tool:
    """Load a single tool or raise if unavailable (used before execution)."""
    module = importlib.import_module(module_path)
    return getattr(module, name)
