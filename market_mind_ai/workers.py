"""
Market Mind AI workers: agent factory and persona definitions.

Each stage emits JSON matching a Pydantic contract in `market_mind_ai.models`.
`create_agents()` is the supported entry point; the module-level names are
kept as lazy, backwards-compatible aliases.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from market_mind_ai.prompts import (
    DIRECTOR_FINAL_DECISION_PROMPT,
    DIRECTOR_PROMPT,
    EXECUTION_JSON_SCHEMA,
    EXECUTION_PROMPT,
    QUANT_JSON_SCHEMA,
    QUANT_PROMPT,
    RISK_JSON_SCHEMA,
    RISK_PROMPT,
    SENTIMENT_JSON_SCHEMA,
    SENTIMENT_PROMPT,
)
from market_mind_ai.tools.tools_registry import (
    get_execution_tools,
    get_market_data_tools,
    get_research_tools,
)

_LEGACY_NAMES = {
    "sentiment_agent": "sentiment",
    "risk_agent": "risk",
    "execution_agent": "execution",
    "quant_agent": "quant",
    "director_agent": "__legacy_director__",
}

_DEFAULT_AGENTS: Dict[str, Any] | None = None
_LEGACY_DIRECTOR: Any = None


def _system_suffix() -> str:
    """Fresh 'current time' hint for agent system prompts."""
    now = datetime.now()
    line = now.strftime("%A, %B %d, %Y at %H:%M")
    if now.tzinfo:
        line += f" {now.tzname() or ''}"
    return f"\n\nCurrent date and time (use this as now): {line.strip()}"


def create_agents(enable_trading: bool = False) -> Dict[str, Any]:
    """
    Build the pipeline agents.

    Args:
        enable_trading: when True, the execution agent receives the Jupiter
            Ultra tools. Live order submission still requires an explicit
            `MarketMindAI(enable_trading=True, dry_run=False)` call site.

    Returns:
        Dict keyed by stage: director, sentiment, quant, risk, execution.
    """
    from swarms import Agent  # lazy: keeps import market_mind_ai dependency-light

    suffix = _system_suffix()
    research_tools = get_research_tools()
    market_tools = get_market_data_tools()
    execution_tools = get_execution_tools() if enable_trading else []

    sentiment_agent = Agent(
        agent_name="Sentiment-Agent",
        system_prompt=SENTIMENT_PROMPT + "\n\n" + SENTIMENT_JSON_SCHEMA + suffix,
        model_name="gpt-4o-mini",
        verbose=True,
        max_loops=1,
        tools=research_tools,
        output_type="str",
    )

    quant_agent = Agent(
        agent_name="Quant-Analyst",
        system_prompt=QUANT_PROMPT.strip()
        + "\n\n" + QUANT_JSON_SCHEMA + suffix,
        model_name="gpt-4.1",
        output_type="str",
        max_loops=1,
        verbose=True,
        context_length=16000,
        tools=market_tools,
    )

    risk_agent = Agent(
        agent_name="Risk-Manager",
        system_prompt=RISK_PROMPT.strip()
        + "\n\n" + RISK_JSON_SCHEMA + suffix,
        model_name="gpt-4.1",
        output_type="str",
        max_loops=1,
        verbose=True,
        context_length=16000,
        tools=market_tools,
    )

    execution_agent = Agent(
        agent_name="Execution-Agent",
        system_prompt=EXECUTION_PROMPT.strip()
        + "\n\n" + EXECUTION_JSON_SCHEMA + suffix,
        model_name="gpt-4.1",
        output_type="str",
        max_loops=1,
        verbose=True,
        context_length=16000,
        tools=execution_tools,
    )

    director_agent = Agent(
        agent_name="Trading-Director",
        system_prompt=DIRECTOR_PROMPT + DIRECTOR_FINAL_DECISION_PROMPT + suffix,
        model_name="gpt-4.1",
        max_loops=1,
        verbose=True,
        context_length=16000,
        tools=research_tools + market_tools,
    )

    return {
        "director": director_agent,
        "sentiment": sentiment_agent,
        "quant": quant_agent,
        "risk": risk_agent,
        "execution": execution_agent,
    }


def get_default_agents() -> Dict[str, Any]:
    """Cached default agent set (safe, no trading tools attached)."""
    global _DEFAULT_AGENTS
    if _DEFAULT_AGENTS is None:
        _DEFAULT_AGENTS = create_agents(enable_trading=False)
    return _DEFAULT_AGENTS


def _get_legacy_director() -> Any:
    """Recreate the old handoff-enabled director for legacy callers."""
    global _LEGACY_DIRECTOR
    if _LEGACY_DIRECTOR is None:
        from swarms import Agent

        agents = get_default_agents()
        handoffs: List[Any] = [
            agents["sentiment"],
            agents["risk"],
            agents["execution"],
            agents["quant"],
        ]
        _LEGACY_DIRECTOR = Agent(
            agent_name="Trading-Director",
            system_prompt=DIRECTOR_PROMPT + _system_suffix(),
            model_name="gpt-4.1",
            max_loops=1,
            handoffs=handoffs,
        )
    return _LEGACY_DIRECTOR


def __getattr__(name: str) -> Any:
    """Lazy aliases for the old module-level agent names."""
    key = _LEGACY_NAMES.get(name)
    if key == "__legacy_director__":
        return _get_legacy_director()
    if key is not None:
        return get_default_agents()[key]
    if name == "ALL_AGENTS":
        agents = get_default_agents()
        return [agents[k] for k in ("sentiment", "risk", "execution", "quant")]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
