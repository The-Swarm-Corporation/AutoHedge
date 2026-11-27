"""
Stocks API client for ticker overview, balance sheets, and daily OHLC.
Uses Massive API (https://massive.com/docs). Set MASSIVE_API_KEY and optionally
POLYGON_BASE_URL in .env.
"""

import json
import os
from typing import Any, Optional

import httpx
from loguru import logger

DEFAULT_BASE_URL = "https://api.massive.com"


def _get_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    key = os.getenv("MASSIVE_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _get(
    path: str,
    *,
    params: Optional[dict[str, Any]] = None,
) -> str:
    url = f"{DEFAULT_BASE_URL.rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                url,
                params=params,
                headers=_get_headers() or None,
            )
            resp.raise_for_status()
            return json.dumps(resp.json())
    except httpx.HTTPError as e:
        logger.error(f"Polygon API request failed: {e}")
        raise


def get_ticker_overview(
    ticker: str, date: Optional[str] = None
) -> str:
    """
    Get comprehensive details for a single ticker (company fundamentals, exchange,
    identifiers, market cap, branding, etc.).

    Parameters
    ----------
    ticker : str
        Case-sensitive ticker symbol (e.g. AAPL for Apple Inc.).
    date : str, optional
        Point-in-time date (YYYY-MM-DD) for ticker info. Defaults to most recent.

    Returns
    -------
    str
        JSON string of the response (results object with active, address, branding,
        cik, description, market_cap, name, primary_exchange, etc.).
    """
    if not ticker or not ticker.strip():
        logger.warning("get_ticker_overview: ticker is empty")
        return "{}"
    path = f"/v3/reference/tickers/{ticker.strip()}"
    params: dict[str, Any] = {}
    if date:
        params["date"] = date
    return _get(path, params=params if params else None)


def get_balance_sheets(
    *,
    cik: Optional[str] = None,
    tickers: Optional[str] = None,
    tickers_any_of: Optional[str] = None,
    period_end: Optional[str] = None,
    period_end_gte: Optional[str] = None,
    period_end_lte: Optional[str] = None,
    filing_date: Optional[str] = None,
    fiscal_year: Optional[float] = None,
    fiscal_quarter: Optional[float] = None,
    timeframe: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
) -> str:
    """
    Get balance sheet data for public companies (quarterly/annual). Returns asset,
    liability, and equity positions as of period end.

    Parameters
    ----------
    cik : str, optional
        SEC Central Index Key (CIK).
    tickers : str, optional
        Filter by ticker(s).
    tickers_any_of : str, optional
        Comma-separated tickers; filter for any of these.
    period_end : str, optional
        Period end date (YYYY-MM-DD).
    period_end_gte, period_end_lte : str, optional
        Period end date range (YYYY-MM-DD).
    filing_date : str, optional
        SEC filing date (YYYY-MM-DD).
    fiscal_year, fiscal_quarter : float, optional
        Fiscal year and quarter (1–4).
    timeframe : str, optional
        'quarterly' or 'annual'.
    limit : int, optional
        Max results (default 100, max 50000).
    sort : str, optional
        Sort columns, e.g. 'period_end.desc'.

    Returns
    -------
    str
        JSON string of the response (results array and next_url if paginated).
    """
    params: dict[str, Any] = {}
    if cik is not None:
        params["cik"] = cik
    if tickers is not None:
        params["tickers"] = tickers
    if tickers_any_of is not None:
        params["tickers.any_of"] = tickers_any_of
    if period_end is not None:
        params["period_end"] = period_end
    if period_end_gte is not None:
        params["period_end.gte"] = period_end_gte
    if period_end_lte is not None:
        params["period_end.lte"] = period_end_lte
    if filing_date is not None:
        params["filing_date"] = filing_date
    if fiscal_year is not None:
        params["fiscal_year"] = fiscal_year
    if fiscal_quarter is not None:
        params["fiscal_quarter"] = fiscal_quarter
    if timeframe is not None:
        params["timeframe"] = timeframe
    if limit is not None:
        params["limit"] = limit
    if sort is not None:
        params["sort"] = sort
    return _get(
        "/stocks/financials/v1/balance-sheets", params=params or None
    )


def get_daily_ticker_summary(
    stocks_ticker: str,
    date: str,
    adjusted: Optional[bool] = None,
) -> str:
    """
    Get daily open/close (OHLC) and volume for a stock ticker on a given date.
    Optionally includes pre-market and after-hours prices.

    Parameters
    ----------
    stocks_ticker : str
        Case-sensitive ticker symbol (e.g. AAPL).
    date : str
        Date of the open/close in YYYY-MM-DD.
    adjusted : bool, optional
        If True, results are adjusted for splits; if False, not adjusted.
        Default from API is adjusted.

    Returns
    -------
    str
        JSON string of the response (open, high, low, close, volume, afterHours,
        preMarket, symbol, from, status).
    """
    if not stocks_ticker or not stocks_ticker.strip():
        logger.warning(
            "get_daily_ticker_summary: stocks_ticker is empty"
        )
        return "{}"
    if not date or not date.strip():
        logger.warning("get_daily_ticker_summary: date is empty")
        return "{}"
    path = f"/v1/open-close/{stocks_ticker.strip()}/{date.strip()}"
    params: dict[str, Any] = {}
    if adjusted is not None:
        params["adjusted"] = "true" if adjusted else "false"
    return _get(path, params=params if params else None)
