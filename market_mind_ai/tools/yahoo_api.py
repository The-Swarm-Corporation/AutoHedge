"""
Yahoo Finance API client for stock quotes, fundamentals, and historical OHLC.
Uses the yfinance package (https://github.com/ranaroussi/yfinance).
Handles Yahoo rate limits (429) by fetching history first and returning
partial data when quoteSummary fails.
"""

import json
import traceback
from typing import Any, Optional

import yfinance as yf
from loguru import logger

# Errors from yfinance when Yahoo returns 429 or non-JSON (rate limit / block)
_RATE_LIMIT_EXCEPTIONS: tuple = (json.JSONDecodeError,)
try:
    import requests

    _RATE_LIMIT_EXCEPTIONS = (
        *_RATE_LIMIT_EXCEPTIONS,
        requests.HTTPError,
    )
except ImportError:
    pass


def _df_to_json_serializable(df: Any) -> Any:
    """Convert DataFrame to a JSON-serializable structure (handles NaN/dates)."""
    if df is None or (hasattr(df, "empty") and df.empty):
        return None
    try:
        import pandas as pd

        if isinstance(df, pd.DataFrame):
            return json.loads(
                df.to_json(orient="split", date_format="iso")
            )
        return df
    except Exception:
        return None


def _safe_info(
    ticker: yf.Ticker,
) -> tuple[dict[str, Any], Optional[str]]:
    """
    Get ticker.info; on 429/JSON error return {} and an error message.
    Returns (info_dict, error_message_or_None).
    """
    try:
        info = ticker.info
        return (info or {}), None
    except _RATE_LIMIT_EXCEPTIONS as e:
        logger.warning(
            "Yahoo rate limit or invalid response (info): {}",
            e,
        )
        return (
            {},
            "Rate limited or invalid response from Yahoo (429).",
        )
    except Exception as e:
        logger.debug("get info failed: {}", e)
        return {}, str(e)


def _safe_financials(ticker: yf.Ticker) -> dict[str, Any]:
    """
    Get balance_sheet, income_stmt, cashflow, etc.; on failure return
    dict with only keys that succeeded and an optional _error key.
    """
    out: dict[str, Any] = {}
    attrs = [
        ("balance_sheet", "balance_sheet"),
        ("quarterly_balance_sheet", "quarterly_balance_sheet"),
        ("income_stmt", "income_stmt"),
        ("quarterly_income_stmt", "quarterly_income_stmt"),
        ("cashflow", "cashflow"),
        ("quarterly_cashflow", "quarterly_cashflow"),
        ("recommendations", "recommendations"),
        ("calendar", "calendar"),
    ]
    for name, attr in attrs:
        try:
            val = getattr(ticker, attr, None)
            if val is not None:
                if hasattr(val, "to_json"):
                    out[name] = _df_to_json_serializable(val)
                else:
                    out[name] = val
        except _RATE_LIMIT_EXCEPTIONS:
            continue
        except Exception:
            continue
    return out


def get_stock_quote(ticker: str) -> str:
    """
    Get current quote for a symbol (price, volume, day range, etc.).
    Fetches history first (chart API); info (quoteSummary) may be empty
    if Yahoo rate-limits.
    """
    if not ticker or not ticker.strip():
        logger.warning("get_stock_quote: ticker is empty")
        return "{}"
    symbol = ticker.strip().upper()
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d", interval="1d")
        info, info_err = _safe_info(t)
        out: dict[str, Any] = {"symbol": symbol, "info": info}
        if info_err:
            out["_warning"] = info_err
        if hist is not None and not hist.empty:
            out["history"] = _df_to_json_serializable(hist)
        return json.dumps(out, default=str)
    except Exception as e:
        logger.error(
            "get_stock_quote failed: {}\n{}",
            e,
            traceback.format_exc(),
        )
        return "{}"


def get_historical_prices(
    ticker: str,
    interval: str = "1d",
    range_str: str = "1mo",
) -> str:
    """
    Get historical OHLCV for a ticker.

    Parameters
    ----------
    ticker : str
        Ticker symbol (e.g. AAPL).
    interval : str, optional
        Candle interval: 1m, 2m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo. Default 1d.
    range_str : str, optional
        Range: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max. Default 1mo.

    Returns
    -------
    str
        JSON string with history (dates, open, high, low, close, volume).
    """
    if not ticker or not ticker.strip():
        logger.warning("get_historical_prices: ticker is empty")
        return "{}"
    symbol = ticker.strip().upper()
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=range_str, interval=interval)
        out: dict[str, Any] = {"symbol": symbol}
        out["history"] = _df_to_json_serializable(hist)
        return json.dumps(out, default=str)
    except Exception as e:
        logger.error(
            "get_historical_prices failed: {}\n{}",
            e,
            traceback.format_exc(),
        )
        return "{}"


def get_quote_summary(
    ticker: str,
    modules: Optional[list[str]] = None,
) -> str:
    """
    Get quote summary (fundamentals, financials, profile, balance sheet,
    income, cashflow). The modules argument is ignored. Uses safe fetchers
    so rate limits (429) return partial data instead of failing.
    """
    if not ticker or not ticker.strip():
        logger.warning("get_quote_summary: ticker is empty")
        return "{}"
    symbol = ticker.strip().upper()
    try:
        t = yf.Ticker(symbol)
        info, info_err = _safe_info(t)
        out: dict[str, Any] = {"symbol": symbol, "info": info}
        if info_err:
            out["_warning"] = info_err
        financials = _safe_financials(t)
        out.update(financials)
        return json.dumps(out, default=str)
    except Exception as e:
        logger.error(
            "get_quote_summary failed: {}\n{}",
            e,
            traceback.format_exc(),
        )
        return "{}"


def get_all_stock_data(
    ticker: str,
    include_history: bool = True,
    history_range: str = "1mo",
) -> str:
    """
    Get all main data for a stock: current quote (info), historical OHLC,
    and quote summary. Fetches history first (chart API); if Yahoo
    rate-limits quoteSummary (429), still returns history and partial data.
    """
    if not ticker or not ticker.strip():
        logger.warning("get_all_stock_data: ticker is empty")
        return "{}"
    symbol = ticker.strip().upper()
    try:
        t = yf.Ticker(symbol)
        # Fetch history first (chart API is less rate-limited than quoteSummary)
        hist = t.history(period=history_range, interval="1d")
        history_serialized = _df_to_json_serializable(hist)

        info, info_err = _safe_info(t)
        if info_err:
            logger.warning(
                "get_all_stock_data: info fetch failed: {}", info_err
            )

        quote_data: dict[str, Any] = {"symbol": symbol, "info": info}
        if info_err:
            quote_data["_warning"] = info_err
        if include_history and history_serialized:
            quote_data["history"] = history_serialized

        summary_data: dict[str, Any] = {
            "symbol": symbol,
            "info": info,
        }
        if info_err:
            summary_data["_warning"] = info_err
        summary_data.update(_safe_financials(t))

        out: dict[str, Any] = {
            "symbol": symbol,
            "quote": quote_data,
            "quote_summary": summary_data,
        }
        if include_history:
            out["history"] = history_serialized

        return json.dumps(out, default=str)
    except Exception as e:
        logger.error(
            "get_all_stock_data failed: {}\n{}",
            e,
            traceback.format_exc(),
        )
        return "{}"


if __name__ == "__main__":
    print(get_all_stock_data("AAPL"))
