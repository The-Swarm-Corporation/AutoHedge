"""
AutoHedge workers: Pydantic output models and agents for thesis
generation, risk assessment, execution, and quantitative analysis.
"""

import os
from datetime import datetime

from swarms import Agent

from autohedge.prompts import (
    DIRECTOR_PROMPT,
    EXECUTION_PROMPT,
    QUANT_PROMPT,
    RISK_PROMPT,
    SENTIMENT_PROMPT,
)
from autohedge.tools.exa_search_tool import exa_search

_NOW = datetime.now()
# Exact date and time for all agent system prompts (simple, single line)
_DATE_TIME_LINE = _NOW.strftime("%A, %B %d, %Y at %H:%M")
if _NOW.tzinfo:
    _DATE_TIME_LINE += f" {_NOW.tzname() or ''}"
_SYSTEM_SUFFIX = f"\n\nCurrent date and time (use this as now): {_DATE_TIME_LINE.strip()}"


def _llm_kwargs(default_model: str) -> dict:
    """Agent ``model_name`` + endpoint, overridable via env.

    With no env set this returns exactly the previously hardcoded
    values, so OpenAI users see no change.  ``AUTOHEDGE_MODEL`` points
    every agent at another model, and ``AUTOHEDGE_LLM_BASE_URL`` (or
    the standard ``OPENAI_BASE_URL`` / ``OPENAI_API_BASE``) sends
    it to any OpenAI-compatible server: a LiteLLM gateway, vLLM,
    Ollama, OpenRouter, and so on.  That makes it possible to run
    AutoHedge entirely on a local or self-hosted model.

    Two details matter for custom endpoints, both verified against a
    LiteLLM proxy:

    * swarms >= 16 routes through LiteLLM and reads the endpoint from
      the Agent parameters ``llm_base_url`` / ``llm_api_key`` --
      ``base_url`` and ``api_key`` are accepted but ignored.
    * Model ids need a LiteLLM provider prefix, e.g.
      ``openai/local-deep``.  The prefix is stripped before the
      request, so the server still receives ``local-deep``; a bare id
      fails with "LLM Provider NOT provided".
    """
    model = os.getenv("AUTOHEDGE_MODEL", default_model)
    kwargs: dict = {"model_name": model}
    base = (
        os.getenv("AUTOHEDGE_LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENAI_API_BASE")
    )
    key = os.getenv("AUTOHEDGE_LLM_API_KEY") or os.getenv(
        "OPENAI_API_KEY"
    )
    if base:
        kwargs["llm_base_url"] = base
    if key:
        kwargs["llm_api_key"] = key
    return kwargs


sentiment_agent = Agent(
    agent_name="Sentiment-Agent",
    system_prompt=SENTIMENT_PROMPT + _SYSTEM_SUFFIX,
    **_llm_kwargs("gpt-4o-mini"),
    verbose=True,
    max_loops=1,
    tools=[exa_search],
)

risk_agent = Agent(
    agent_name="Risk-Manager",
    system_prompt=RISK_PROMPT.strip()
    + "\n\nWhen you receive a message, it will contain:\nStock, Thesis, Quant Analysis.\n\nProvide risk assessment including:\n1. Recommended position size\n2. Maximum drawdown risk\n3. Market risk exposure\n4. Overall risk score"
    + _SYSTEM_SUFFIX,
    **_llm_kwargs("gpt-4.1"),
    output_type="str",
    max_loops=1,
    verbose=True,
    context_length=16000,
)

execution_agent = Agent(
    agent_name="Execution-Agent",
    system_prompt=EXECUTION_PROMPT.strip()
    + "\n\nWhen you receive a message, it will contain:\nStock, Thesis, Risk Assessment.\n\nGenerate trade order including:\n1. Order type (market/limit)\n2. Quantity\n3. Entry price\n4. Stop loss\n5. Take profit\n6. Time in force"
    + _SYSTEM_SUFFIX,
    **_llm_kwargs("gpt-4.1"),
    output_type="str",
    max_loops=1,
    verbose=True,
    context_length=16000,
)

quant_agent = Agent(
    agent_name="Quant-Analyst",
    system_prompt=QUANT_PROMPT.strip()
    + "\n\nWhen you receive a message, it will contain:\nStock and Thesis from your Director.\n\nGenerate quantitative analysis with: ticker, technical_score (0-1), volume_score (0-1), trend_strength (0-1), volatility, probability_score (0-1), key_levels (support, resistance, pivot)."
    + _SYSTEM_SUFFIX,
    **_llm_kwargs("gpt-4.1"),
    output_type="str",
    max_loops=1,
    verbose=True,
    context_length=16000,
)


ALL_AGENTS = [
    sentiment_agent,
    risk_agent,
    execution_agent,
    quant_agent,
]


director_agent = Agent(
    agent_name="Trading-Director",
    system_prompt=DIRECTOR_PROMPT + _SYSTEM_SUFFIX,
    **_llm_kwargs("gpt-4.1"),
    max_loops=1,
    handoffs=ALL_AGENTS,
)


if __name__ == "__main__":
    output = director_agent.run(
        "Analyze the stock market and provide a thesis on the overall market position and expected trends."
    )
    print(output)
