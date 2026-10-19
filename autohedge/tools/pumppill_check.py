"""
PumpPill pre-trade check – one risk decision for a Solana token before a buy.
API docs: https://www.pumppill.org/for-agents (GET /api/pretrade/{mint}).

No API key. Read-only: the answer comes from PumpPill's stored read of the
token (can it be sold, can the deployer still mint or freeze, bundled or
coordinated launch buyers, how far it has already run) and never places or
simulates a trade.
"""

import json
import os

import httpx
from loguru import logger

PUMPPILL_API_BASE = os.getenv(
    "PUMPPILL_API_BASE", "https://api.pumppill.org"
)


def pre_trade_check(mint: str) -> str:
    """
    Get PumpPill's pre-trade risk decision for one Solana token mint.

    Parameters
    ----------
    mint : str
        Solana token mint address (base58). A Robinhood Chain 0x contract
        address is also accepted.

    Returns
    -------
    str
        JSON string with:
        - decision: "clear", "caution", "avoid" or "unknown"
        - headline: one sentence summarising the read
        - reasons: list of {level, code, text}, worst first, where level is
          "avoid", "caution" or "ok"
        - symbol, holders, market_cap_usd, read_at, page_url when known

        "avoid" means the token cannot be sold, the deployer can still mint
        or freeze, the launch group is selling, the contract read is high
        risk, or it is no longer trading. "unknown" means PumpPill holds no
        read for the token; treat it as unverified, never as "clear".
        On a network error the JSON is {"decision": "unknown", "error": ...}.

    Examples
    --------
    >>> pre_trade_check("So11111111111111111111111111111111111111112")
    """
    if not mint or not mint.strip():
        logger.warning("pre_trade_check: mint is empty")
        return json.dumps(
            {"decision": "unknown", "error": "empty mint"}
        )

    url = f"{PUMPPILL_API_BASE}/api/pretrade/{mint.strip()}"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                url, headers={"User-Agent": "AutoHedge"}
            )
            resp.raise_for_status()
            return json.dumps(resp.json())
    except httpx.HTTPError as e:
        # A failed check is not a pass: report unknown so the risk
        # agent does not size a position on missing information.
        logger.error(f"PumpPill pre-trade check failed: {e}")
        return json.dumps({"decision": "unknown", "error": str(e)})
