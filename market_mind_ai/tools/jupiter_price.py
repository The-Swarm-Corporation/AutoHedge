"""
Jupiter Price API V3 – fetch token prices on Solana.
API docs: https://dev.jup.ag (see /price/v3).
"""

import json
import os
from typing import List, Union

import httpx
from loguru import logger

JUPITER_PRICE_BASE = "https://api.jup.ag"


def get_token_price(
    ids: Union[str, List[str]],
) -> str:
    """
    Get USD prices for one or more Solana token mint addresses via Jupiter Price API V3.

    Parameters
    ----------
    ids : str or list of str
        Token mint address(es). Pass a single address string or a list of addresses.
        Example: "So11111111111111111111111111111111111111112" (wrapped SOL)
        or ["So11111111111111111111111111111111111111112", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"]
    API key is read from JUPITER_API_KEY in .env (https://portal.jup.ag).

    Returns
    -------
    str
        JSON string of the response: token mint address(es) as keys, each value has at
        least `decimals`, `usdPrice`, and optionally `blockId`, `priceChange24h` and
        other fields. Returns "{}" when ids is empty.

    Raises
    ------
    httpx.HTTPError
        On HTTP/network errors.

    Examples
    --------
    >>> get_token_price("So11111111111111111111111111111111111111112")
    >>> get_token_price(["So11111111111111111111111111111111111111112", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"])
    """
    if isinstance(ids, list):
        ids_param = ",".join(ids)
    else:
        ids_param = ids

    if not ids_param or not ids_param.strip():
        logger.warning("get_token_price: ids is empty")
        return "{}"

    url = f"{JUPITER_PRICE_BASE}/price/v3"
    params = {"ids": ids_param}
    headers = {}

    key = os.getenv("JUPITER_API_KEY")

    if key:
        headers["x-api-key"] = key

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                url, params=params, headers=headers or None
            )
            resp.raise_for_status()
            return json.dumps(resp.json())
    except httpx.HTTPError as e:
        logger.error(f"Jupiter price API request failed: {e}")
        raise
