# Architecture

## Pipeline

`AutoHedge.run(task)` executes:

```
director (ticker discovery)
    -> sentiment -> quant -> risk -> execution (order proposal)
    -> director (final decision)
```

The raw text of each stage is retained in `TickerResult.raw_outputs` for audit.
Each stage's JSON is parsed with `autohedge.models.parse_model` into a typed
model; validation failures are recorded in `TickerResult.errors` and the cycle
continues with whatever context is available.

## Structured contracts

| Stage | Model |
|---|---|
| Sentiment | `SentimentAnalysis` |
| Quant | `QuantAnalysis` |
| Risk | `RiskAssessment` |
| Execution | `TradeOrder` |
| Director decision | `TradeDecision` |
| Full cycle | `CycleResult` |

## Tool wiring

`autohedge/tools/tools_registry.py` groups tools into research, market-data and
execution sets. `autohedge.workers.create_agents()` attaches them to the
appropriate agents. Imports are lazy so a missing optional dependency does not
break the research pipeline.

## Trading safety

Live submission is opt-in at two levels:

- `enable_trading=True` attaches the Jupiter Ultra tools.
- `dry_run=False` actually signs and submits a swap.

Even then, only BUY/SELL decisions with a complete `input_mint`, `output_mint`
and `amount` are submitted. All other decisions remain proposals.
