"""
AutoHedge workers: Pydantic output models and agents for thesis
generation, risk assessment, execution, and quantitative analysis.
"""

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
from autohedge.tools.pumppill_check import pre_trade_check

_NOW = datetime.now()
# Exact date and time for all agent system prompts (simple, single line)
_DATE_TIME_LINE = _NOW.strftime("%A, %B %d, %Y at %H:%M")
if _NOW.tzinfo:
    _DATE_TIME_LINE += f" {_NOW.tzname() or ''}"
_SYSTEM_SUFFIX = f"\n\nCurrent date and time (use this as now): {_DATE_TIME_LINE.strip()}"

sentiment_agent = Agent(
    agent_name="Sentiment-Agent",
    system_prompt=SENTIMENT_PROMPT + _SYSTEM_SUFFIX,
    model_name="gpt-4o-mini",
    verbose=True,
    max_loops=1,
    tools=[exa_search],
)

risk_agent = Agent(
    agent_name="Risk-Manager",
    system_prompt=RISK_PROMPT.strip()
    + "\n\nWhen you receive a message, it will contain:\nStock, Thesis, Quant Analysis.\n\nProvide risk assessment including:\n1. Recommended position size\n2. Maximum drawdown risk\n3. Market risk exposure\n4. Overall risk score"
    + _SYSTEM_SUFFIX,
    model_name="gpt-4.1",
    output_type="str",
    max_loops=1,
    verbose=True,
    context_length=16000,
    tools=[pre_trade_check],
)

execution_agent = Agent(
    agent_name="Execution-Agent",
    system_prompt=EXECUTION_PROMPT.strip()
    + "\n\nWhen you receive a message, it will contain:\nStock, Thesis, Risk Assessment.\n\nGenerate trade order including:\n1. Order type (market/limit)\n2. Quantity\n3. Entry price\n4. Stop loss\n5. Take profit\n6. Time in force"
    + _SYSTEM_SUFFIX,
    model_name="gpt-4.1",
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
    model_name="gpt-4.1",
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
    model_name="gpt-4.1",
    max_loops=1,
    handoffs=ALL_AGENTS,
)


if __name__ == "__main__":
    output = director_agent.run(
        "Analyze the stock market and provide a thesis on the overall market position and expected trends."
    )
    print(output)
