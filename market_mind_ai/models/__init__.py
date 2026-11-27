"""
Structured output contracts for the Market Mind AI agent pipeline.

LLM agents return text; these models are the typed contract between stages.
`parse_model` is intentionally tolerant of the usual LLM output quirks
(markdown fences, leading prose, JSON embedded in a list) while still
validating the payload before it is passed to the next stage.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")

_NON_TICKERS = {
    "USD", "USDC", "SOL", "BTC", "ETH", "AND", "THE", "FOR", "WITH",
    "FROM", "THIS", "THAT", "WHAT", "WHEN", "WHERE", "ANALYZE", "TASK",
    "STOCK", "STOCKS", "MARKET", "TRADE", "BUY", "SELL", "HOLD", "JSON",
    "ONLY", "TRUE", "FALSE", "NULL", "USD", "AI", "CEO", "IPO", "ETF",
}


class KeyLevels(BaseModel):
    """Support / resistance / pivot levels from quantitative analysis."""

    support: Optional[float] = None
    resistance: Optional[float] = None
    pivot: Optional[float] = None


class SentimentAnalysis(BaseModel):
    """Output contract of the Sentiment-Agent."""

    ticker: str
    overall_sentiment_score: Optional[float] = Field(default=None, ge=0, le=1)
    news_sentiment: Optional[str] = None
    social_sentiment: Optional[str] = None
    institutional_sentiment: Optional[str] = None
    key_themes: List[str] = Field(default_factory=list)
    critical_events: List[str] = Field(default_factory=list)
    sentiment_trend: Optional[str] = None
    trading_implications: Optional[str] = None
    contrarian_signals: Optional[str] = None


class QuantAnalysis(BaseModel):
    """Output contract of the Quant-Analyst agent."""

    ticker: str
    technical_score: Optional[float] = Field(default=None, ge=0, le=1)
    volume_score: Optional[float] = Field(default=None, ge=0, le=1)
    trend_strength: Optional[float] = Field(default=None, ge=0, le=1)
    volatility: Optional[float] = None
    probability_score: Optional[float] = Field(default=None, ge=0, le=1)
    key_levels: Optional[KeyLevels] = None
    rationale: Optional[str] = None


class RiskAssessment(BaseModel):
    """Output contract of the Risk-Manager agent."""

    ticker: str
    recommended_position_size: Optional[str] = None
    max_drawdown_risk: Optional[str] = None
    market_risk_exposure: Optional[str] = None
    overall_risk_score: Optional[float] = Field(default=None, ge=0, le=1)
    notes: Optional[str] = None


class TradeOrder(BaseModel):
    """
    Output contract of the Execution-Agent.

    `input_mint` / `output_mint` / `amount` are only required when the
    order is actually submitted to Jupiter Ultra; the agent may propose
    an equity-style order without them (in which case it is a proposal).
    """

    symbol: str
    order_type: Optional[str] = None
    quantity: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_in_force: Optional[str] = None
    input_mint: Optional[str] = None
    output_mint: Optional[str] = None
    amount: Optional[str] = None


class TradeDecision(BaseModel):
    """Final BUY / SELL / HOLD decision produced by the director."""

    ticker: str
    action: str = "HOLD"
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    thesis: Optional[str] = None
    reasoning: Optional[str] = None
    order: Optional[TradeOrder] = None


class TickerResult(BaseModel):
    """All stage outputs and raw text for a single ticker."""

    ticker: str
    sentiment: Optional[SentimentAnalysis] = None
    quant: Optional[QuantAnalysis] = None
    risk: Optional[RiskAssessment] = None
    order: Optional[TradeOrder] = None
    decision: Optional[TradeDecision] = None
    errors: List[str] = Field(default_factory=list)
    raw_outputs: Dict[str, str] = Field(default_factory=dict)


class CycleResult(BaseModel):
    """Result of one complete trading/research cycle."""

    task: str
    tickers: List[str] = Field(default_factory=list)
    results: List[TickerResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    executions: List[Dict[str, Any]] = Field(default_factory=list)


def _extract_json(text: Any) -> Optional[Any]:
    """Pull the first JSON value out of a raw LLM response."""
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None

    fenced = _JSON_FENCE.search(raw)
    if fenced:
        raw = fenced.group(1).strip()

    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        pass

    # Fall back to the first balanced {...} or [...] block in prose.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = raw.find(opener)
        if start < 0:
            continue
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(raw)):
            char = raw[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start : index + 1])
                    except (ValueError, TypeError):
                        break
    return None


def parse_model(
    text: Any,
    model_type: Type[T],
    defaults: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[T], Optional[str]]:
    """
    Validate raw agent output into `model_type`.

    `defaults` supplies fields the agent may have omitted (typically
    `ticker`); keys present in the agent output always win.

    Returns (model, None) on success or (None, error_message) on failure.
    Never raises, so a malformed stage cannot abort the whole cycle.
    """
    data = _extract_json(text)
    if data is None:
        return None, "No valid JSON object found in agent output"
    if isinstance(data, list):
        if not data:
            return None, "Empty JSON list in agent output"
        data = data[0]
    if not isinstance(data, dict):
        return None, f"Expected a JSON object, got {type(data).__name__}"

    if defaults:
        merged = dict(defaults)
        merged.update(data)
        data = merged

    try:
        validate = getattr(model_type, "model_validate", None)
        if validate is not None:  # pydantic v2
            return validate(data), None
        return model_type.parse_obj(data), None  # pydantic v1 fallback
    except Exception as exc:  # ValidationError and friends
        return None, str(exc)


def parse_ticker_list(text: Any) -> Tuple[List[str], Optional[str]]:
    """Parse the director's ticker discovery output into a list of symbols."""
    data = _extract_json(text)
    tickers: List[str] = []
    if isinstance(data, list):
        tickers = [str(item).strip().upper() for item in data if str(item).strip()]
    elif isinstance(data, dict):
        for key in ("tickers", "symbols", "stocks"):
            value = data.get(key)
            if isinstance(value, list):
                tickers = [str(item).strip().upper() for item in value if str(item).strip()]
                break
    else:
        # Last resort: uppercase ticker-like tokens from the prose.
        tickers = [t for t in _TICKER_RE.findall(str(text)) if t not in _NON_TICKERS]

    tickers = list(dict.fromkeys(tickers))[:10]
    if not tickers:
        return [], "No tickers found in director output"
    return tickers, None
