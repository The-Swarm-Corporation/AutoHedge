"""
Market Mind AI orchestration: an explicit, typed agent pipeline.

The pipeline runs director (ticker discovery) -> sentiment -> quant -> risk
-> execution (order proposal) -> director (final decision). Each stage's raw
text is validated into a Pydantic contract before it is passed downstream.

Live order submission is opt-in: `enable_trading=True` attaches the Jupiter
tools, and `dry_run=False` actually submits a signed transaction. The
defaults are safe (research only, no submission).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from market_mind_ai.models import (
    CycleResult,
    QuantAnalysis,
    RiskAssessment,
    SentimentAnalysis,
    TickerResult,
    TradeDecision,
    TradeOrder,
    parse_model,
    parse_ticker_list,
)
from market_mind_ai.prompts import (
    DIRECTOR_FINAL_DECISION_PROMPT,
    DIRECTOR_TICKER_DISCOVERY_PROMPT,
    EXECUTION_ORDER_PROMPT,
    QUANT_ANALYSIS_PROMPT,
    RISK_ASSESSMENT_PROMPT,
    SENTIMENT_TASK_PROMPT,
)
from market_mind_ai.workers import create_agents

MAX_TICKERS = 10
MAX_RAW_CHARS = 8000


def _dump(model: Any) -> str:
    """Serialize a Pydantic model on either v1 or v2."""
    dumper = getattr(model, "model_dump_json", None)
    return dumper() if dumper else model.json()


def _to_dict(model: Any) -> Dict[str, Any]:
    """Convert a Pydantic model to a dict on either v1 or v2."""
    dumper = getattr(model, "model_dump", None)
    return dumper() if dumper else model.dict()


def _execution_succeeded(payload: Dict[str, Any]) -> bool:
    status = str(payload.get("status", "")).lower()
    if status in {"success", "succeeded", "ok", "confirmed"}:
        return True
    if status in {"failed", "error", "false"}:
        return False
    return not payload.get("error") and bool(payload.get("signature"))


class MarketMindAI:
    """Coordinates all agents and manages one trading/research cycle."""

    def __init__(
        self,
        name: str = "market-mind-ai",
        description: str = "fully autonomous hedgefund",
        output_dir: str = "outputs",
        output_file_path: Optional[str] = None,
        output_type: str = "list",
        enable_trading: bool = False,
        dry_run: bool = True,
        agents: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.output_type = output_type
        self.output_file_path = output_file_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Safety first: neither attaching execution tools nor submitting
        # orders happens unless the caller explicitly asks for it.
        self.enable_trading = bool(enable_trading)
        self.dry_run = bool(dry_run)
        self.agents: Dict[str, Any] = agents if agents is not None else {}
        self.last_result: Optional[CycleResult] = None
        self.conversation: Any = None

        try:
            from swarms import Conversation

            self.conversation = Conversation(time_enabled=True)
        except Exception as exc:
            logger.warning("Conversation log unavailable: {}", exc)

        logger.info("Initialized Market Mind AI (trading={}, dry_run={})",
                    self.enable_trading, self.dry_run)

    # ------------------------------------------------------------------ #
    # Agent plumbing
    # ------------------------------------------------------------------ #
    def _record(self, role: str, content: str) -> None:
        if self.conversation is None:
            return
        try:
            self.conversation.add(role=role, content=content)
        except Exception as exc:
            logger.debug("Could not record conversation turn: {}", exc)

    @staticmethod
    def _call_agent(
        agent: Any,
        prompt: str,
        raw_outputs: Dict[str, str],
        stage: str,
    ) -> Optional[str]:
        """Run one stage and keep its raw text for the audit trail."""
        if agent is None:
            raw_outputs[stage] = f"{stage} agent is not configured"
            return None
        try:
            try:
                output = agent.run(prompt)
            except TypeError:
                output = agent.run(task=prompt)
        except Exception as exc:
            message = f"{stage} agent failed: {exc}"
            logger.error(message)
            raw_outputs[stage] = message
            return None

        text = "" if output is None else str(output)
        raw_outputs[stage] = text[:MAX_RAW_CHARS]
        return text

    @staticmethod
    def _parse_stage(
        raw: Optional[str],
        model_type: Any,
        ticker: str,
        stage: str,
        result: TickerResult,
    ) -> Any:
        if raw is None:
            result.errors.append(f"{stage}: no output from agent")
            return None
        parsed, error = parse_model(raw, model_type, defaults={"ticker": ticker})
        if error or parsed is None:
            result.errors.append(f"{stage}: {error or 'empty model output'}")
            return None
        # The stage must describe the ticker this pipeline asked about, even
        # if the model echoed a different symbol from its context.
        if hasattr(parsed, "ticker"):
            parsed.ticker = ticker
        return parsed

    # ------------------------------------------------------------------ #
    # Pipeline stages
    # ------------------------------------------------------------------ #
    def _discover_tickers(self, task: str) -> Tuple[List[str], Optional[str]]:
        raw_outputs: Dict[str, str] = {}
        text = self._call_agent(
            self.agents["director"],
            DIRECTOR_TICKER_DISCOVERY_PROMPT.format(task=task),
            raw_outputs,
            "ticker_discovery",
        )
        tickers, error = parse_ticker_list(text)
        if error:
            logger.warning("Ticker discovery: {}", error)
        return tickers, error

    def _analyze_ticker(self, ticker: str, task: str) -> TickerResult:
        result = TickerResult(ticker=ticker)
        raw = result.raw_outputs

        # 1. Sentiment / news research
        sentiment_raw = self._call_agent(
            self.agents["sentiment"],
            SENTIMENT_TASK_PROMPT.format(ticker=ticker, task=task),
            raw,
            "sentiment",
        )
        result.sentiment = self._parse_stage(
            sentiment_raw, SentimentAnalysis, ticker, "sentiment", result
        )
        thesis = (
            (result.sentiment.trading_implications if result.sentiment else None)
            or (sentiment_raw or "")[:1500]
            or task
        )

        # 2. Quantitative analysis
        quant_raw = self._call_agent(
            self.agents["quant"],
            QUANT_ANALYSIS_PROMPT.format(stock=ticker, thesis=thesis),
            raw,
            "quant",
        )
        result.quant = self._parse_stage(
            quant_raw, QuantAnalysis, ticker, "quant", result
        )

        # 3. Risk assessment
        risk_raw = self._call_agent(
            self.agents["risk"],
            RISK_ASSESSMENT_PROMPT.format(
                stock=ticker,
                thesis=thesis,
                quant_analysis=(
                    _dump(result.quant) if result.quant
                    else (quant_raw or "")[:1500]
                ),
            ),
            raw,
            "risk",
        )
        result.risk = self._parse_stage(
            risk_raw, RiskAssessment, ticker, "risk", result
        )

        # 4. Order proposal (live tools only attached when trading enabled)
        order_raw = self._call_agent(
            self.agents["execution"],
            EXECUTION_ORDER_PROMPT.format(
                stock=ticker,
                thesis=thesis,
                risk_assessment=(
                    _dump(result.risk) if result.risk
                    else (risk_raw or "")[:1500]
                ),
            ),
            raw,
            "execution",
        )
        result.order = self._parse_stage(
            order_raw, TradeOrder, ticker, "execution", result
        )

        # 5. Final director decision
        decision_raw = self._call_agent(
            self.agents["director"],
            DIRECTOR_FINAL_DECISION_PROMPT.format(
                ticker=ticker,
                task=task,
                thesis=thesis,
                quant_analysis=(
                    _dump(result.quant) if result.quant
                    else (quant_raw or "")[:1000]
                ),
                risk_assessment=(
                    _dump(result.risk) if result.risk
                    else (risk_raw or "")[:1000]
                ),
                order=_dump(result.order) if result.order else "None",
            ),
            raw,
            "decision",
        )
        result.decision = self._parse_stage(
            decision_raw, TradeDecision, ticker, "decision", result
        )
        if result.decision is not None:
            result.decision.ticker = ticker
            action = (result.decision.action or "HOLD").upper()
            if action not in {"BUY", "SELL", "HOLD"}:
                result.errors.append(
                    f"decision: unknown action {action!r}, defaulting to HOLD"
                )
                action = "HOLD"
            result.decision.action = action

        return result

    # ------------------------------------------------------------------ #
    # Execution (explicit opt-in)
    # ------------------------------------------------------------------ #
    def execute_decision(self, decision: TradeDecision) -> Dict[str, Any]:
        """Submit a decision to Jupiter Ultra, subject to the safety gates."""
        if not self.enable_trading:
            return {"status": "SKIPPED", "reason": "trading is disabled"}
        if self.dry_run:
            return {"status": "SIMULATED", "decision": _to_dict(decision)}

        order = decision.order
        if (
            order is None
            or not order.input_mint
            or not order.output_mint
            or not order.amount
        ):
            return {
                "status": "SKIPPED",
                "reason": "decision has no complete swap parameters",
            }

        try:
            from market_mind_ai.tools.tools_registry import load_tool

            get_order = load_tool("market_mind_ai.tools.ultra_tools", "get_order")
            execute_trade = load_tool(
                "market_mind_ai.tools.ultra_tools", "execute_trade"
            )
            quote = json.loads(
                get_order(order.input_mint, order.output_mint, str(order.amount))
            )
            transaction = quote.get("transaction")
            request_id = quote.get("requestId") or quote.get("request_id")
            if not transaction or not request_id:
                return {
                    "status": "FAILED",
                    "reason": "incomplete order response",
                    "quote_keys": sorted(quote),
                }
            response = json.loads(execute_trade(transaction, str(request_id)))
            succeeded = _execution_succeeded(response)
            logger.info("Trade execution status: {}", response.get("status"))
            return {
                "status": "EXECUTED" if succeeded else "FAILED",
                "result": response,
            }
        except Exception as exc:
            logger.error("Trade execution failed: {}", exc)
            return {"status": "FAILED", "reason": str(exc)}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def run(self, task: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute one complete trading cycle.

        Returns a dict/list/JSON string depending on `output_type`; the
        full typed `CycleResult` is always available as `self.last_result`.
        Set `strict=True` to re-raise fatal errors instead of recording them.
        """
        cycle = CycleResult(task=str(task))
        self._record("user", f"Task: {task}")
        logger.info("Starting trading cycle")

        try:
            if not self.agents:
                self.agents = create_agents(enable_trading=self.enable_trading)

            tickers, error = self._discover_tickers(task)
            cycle.tickers = tickers
            if error:
                cycle.errors.append(f"ticker_discovery: {error}")

            for ticker in tickers:
                cycle.results.append(self._analyze_ticker(ticker, task))

            if self.enable_trading:
                for ticker_result in cycle.results:
                    decision = ticker_result.decision
                    if decision and decision.action in {"BUY", "SELL"}:
                        cycle.executions.append(
                            self.execute_decision(decision)
                        )
        except Exception as exc:
            cycle.errors.append(str(exc))
            logger.error("Error in trading cycle: {}", exc, exc_info=True)
            if kwargs.get("strict", False):
                raise

        self.last_result = cycle
        self._record("director", _dump(cycle)[:MAX_RAW_CHARS])

        if self.output_file_path:
            Path(self.output_file_path).write_text(_dump(cycle))

        if self.output_type == "dict":
            return _to_dict(cycle)
        if self.output_type == "str":
            return _dump(cycle)
        return [_to_dict(result) for result in cycle.results]
