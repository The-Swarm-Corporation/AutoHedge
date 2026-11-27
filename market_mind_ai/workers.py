"""
Market Mind AI workers: agent factory and persona definitions.

Each stage emits JSON matching a Pydantic contract in `market_mind_ai.models`.
`create_agents()` is the supported entry point; the module-level names are
kept as lazy, backwards-compatible aliases.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from market_mind_ai.env_loader import qwen_is_configured
from market_mind_ai.models.qwen_model import QwenModel
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
_QWEN_MODEL: Optional[QwenModel] = None


def _use_qwen() -> bool:
    """Return True when Qwen2.5 is configured and should be used."""
    return qwen_is_configured()


def _get_qwen_model() -> Optional[QwenModel]:
    """Lazily create and cache a QwenModel instance."""
    global _QWEN_MODEL
    if _QWEN_MODEL is None:
        if _use_qwen():
            _QWEN_MODEL = QwenModel()
        else:
            _QWEN_MODEL = None
    return _QWEN_MODEL


def _system_suffix() -> str:
    """Fresh 'current time' hint for agent system prompts."""
    now = datetime.now()
    line = now.strftime("%A, %B %d, %Y at %H:%M")
    if now.tzinfo:
        line += f" {now.tzname() or ''}"
    return (
        f"\n\nCurrent date and time (use this as now): {line.strip()}"
    )


def create_agents(enable_trading: bool = False) -> Dict[str, Any]:
    """
    Build the pipeline agents.

    When ``QWEN_API_KEY`` is set in the environment, agents use the
    Qwen2.5-1.5B Instruct model via ``llm_base_url``/``llm_api_key`` on the
    swarms Agent. Otherwise they fall back to the default OpenAI models
    (gpt-4o-mini / gpt-4.1) for backwards compatibility.

    Args:
        enable_trading: when True, the execution agent receives the Jupiter
            Ultra tools. Live order submission still requires an explicit
            `MarketMindAI(enable_trading=True, dry_run=False)` call site.

    Returns:
        Dict keyed by stage: director, sentiment, quant, risk, execution.
    """
    from swarms import (
        Agent,
    )  # lazy: keeps import market_mind_ai dependency-light

    suffix = _system_suffix()
    research_tools = get_research_tools()
    market_tools = get_market_data_tools()
    execution_tools = get_execution_tools() if enable_trading else []

    qwen_model = _get_qwen_model()

    def _agent_kwargs(model_name: str) -> Dict[str, Any]:
        """Common Agent kwargs; injects Qwen llm when configured."""
        kwargs: Dict[str, Any] = {
            "verbose": True,
            "max_loops": 1,
            "output_type": "str",
        }
        if qwen_model is not None and qwen_model.is_available:
            kwargs["llm"] = qwen_model
            kwargs["model_name"] = qwen_model.model or model_name
        else:
            kwargs["model_name"] = model_name
        return kwargs

    sentiment_agent = Agent(
        agent_name="Sentiment-Agent",
        system_prompt=SENTIMENT_PROMPT
        + "\n\n"
        + SENTIMENT_JSON_SCHEMA
        + suffix,
        tools=research_tools,
        **_agent_kwargs("gpt-4o-mini"),
    )

    quant_agent = Agent(
        agent_name="Quant-Analyst",
        system_prompt=QUANT_PROMPT.strip()
        + "\n\n"
        + QUANT_JSON_SCHEMA
        + suffix,
        tools=market_tools,
        context_length=16000,
        **_agent_kwargs("gpt-4.1"),
    )

    risk_agent = Agent(
        agent_name="Risk-Manager",
        system_prompt=RISK_PROMPT.strip()
        + "\n\n"
        + RISK_JSON_SCHEMA
        + suffix,
        tools=market_tools,
        context_length=16000,
        **_agent_kwargs("gpt-4.1"),
    )

    execution_agent = Agent(
        agent_name="Execution-Agent",
        system_prompt=EXECUTION_PROMPT.strip()
        + "\n\n"
        + EXECUTION_JSON_SCHEMA
        + suffix,
        tools=execution_tools,
        context_length=16000,
        **_agent_kwargs("gpt-4.1"),
    )

    director_agent = Agent(
        agent_name="Trading-Director",
        system_prompt=DIRECTOR_PROMPT
        + DIRECTOR_FINAL_DECISION_PROMPT
        + suffix,
        tools=research_tools + market_tools,
        context_length=16000,
        **_agent_kwargs("gpt-4.1"),
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
        return [
            agents[k]
            for k in ("sentiment", "risk", "execution", "quant")
        ]
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
