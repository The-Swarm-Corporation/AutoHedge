# AutoHedge

AutoHedge is an autonomous multi-agent trading research framework. It runs an
explicit pipeline:

1. **Director** — discovers relevant tickers from the task and makes the final
   BUY / SELL / HOLD decision.
2. **Sentiment** — news and social sentiment (Exa search).
3. **Quant** — technical, volume and trend scoring (Yahoo / Massive / Jupiter).
4. **Risk** — position sizing, drawdown and exposure assessment.
5. **Execution** — produces a structured order proposal.

Every stage emits JSON validated against the Pydantic contracts in
`autohedge/models.py`, so a malformed agent response cannot corrupt downstream
stages.

## Quick start

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=...
python -m autohedge
```

```python
from autohedge import AutoHedge

system = AutoHedge()  # research only; no live trading
system.run("Analyze NVDA for a 50k allocation")
print(system.last_result)
```

See [Architecture](architecture.md) for details on the pipeline and the
trading safety gates.
