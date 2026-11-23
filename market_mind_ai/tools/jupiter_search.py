"""
Jupiter Tokens API V2 – search tokens by symbol, name or mint address.
API docs: https://dev.jup.ag (see /tokens/v2/search).
"""

import json
import os

import httpx
from loguru import logger

JUPITER_TOKENS_BASE = "https://api.jup.ag/tokens/v2"


def search_tokens(query: str) -> str:
    """
    Search for Solana tokens by symbol, name, or mint address via Jupiter Tokens API V2.
    API key is read from JUPITER_API_KEY in .env (https://portal.jup.ag).

    Parameters
    ----------
    query : str
        Search string: token symbol, name, or mint address.
        Use comma-separated mint addresses to look up multiple mints (max 100).
        Symbol/name search returns up to 20 results by default.

    Returns
    -------
    str
        JSON string: array of token info objects (id, name, symbol, icon, decimals,
        holderCount, fdv, mcap, usdPrice, liquidity, organicScore, isVerified, tags,
        etc.). Returns "[]" when query is empty.

    Raises
    ------
    httpx.HTTPError
        On HTTP/network errors.

    Examples
    --------
    >>> search_tokens("USDC")
    >>> search_tokens("So11111111111111111111111111111111111111112")
    >>> search_tokens("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v,So11111111111111111111111111111111111111112")
    """
    if not query or not query.strip():
        logger.warning("search_tokens: query is empty")
        return "[]"

    url = f"{JUPITER_TOKENS_BASE}/search"
    params = {"query": query.strip()}
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
        logger.error(f"Jupiter tokens search request failed: {e}")
        raise
