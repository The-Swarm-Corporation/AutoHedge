"""FXMacroData macroeconomic release-calendar tool."""

import json
import os
from typing import Any, Optional

import httpx
from loguru import logger

DEFAULT_BASE_URL = "https://fxmacrodata.com/api/v1"


def get_macro_release_calendar(
    currency: str = "usd",
    limit: int = 20,
    min_tier: Optional[int] = 2,
) -> str:
    """
    Get macroeconomic and central-bank release events for a currency.

    Parameters
    ----------
    currency : str
        Three-letter currency code such as USD, EUR, JPY, or GBP.
    limit : int
        Maximum number of events to return.
    min_tier : int, optional
        Maximum market tier to include. The default keeps tier 1 and 2 events.
    """
    params: dict[str, Any] = {"limit": max(1, int(limit))}
    api_key = os.getenv("FXMACRODATA_API_KEY")
    if api_key:
        params["api_key"] = api_key

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{DEFAULT_BASE_URL}/calendar/{currency.lower()}",
                params=params,
            )
            response.raise_for_status()
            rows = response.json().get("data", [])
    except httpx.HTTPError as exc:
        logger.error(f"FXMacroData request failed: {exc}")
        raise

    if min_tier is not None:
        rows = [
            row
            for row in rows
            if int(row.get("market_tier") or 99) <= int(min_tier)
        ]

    return json.dumps({"currency": currency.upper(), "events": rows[: int(limit)]})
