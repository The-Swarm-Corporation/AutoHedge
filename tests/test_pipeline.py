import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from market_mind_ai.main import MarketMindAI
from market_mind_ai.models import CycleResult


DEFAULT_SENTIMENT = {
    "ticker": "NVDA",
    "overall_sentiment_score": 0.8,
    "trading_implications": "Bullish momentum",
}

DEFAULT_QUANT = {
    "ticker": "NVDA",
    "technical_score": 0.7,
    "volume_score": 0.6,
    "trend_strength": 0.75,
    "probability_score": 0.65,
    "key_levels": {"support": 100.0, "resistance": 120.0, "pivot": 110.0},
}

DEFAULT_RISK = {
    "ticker": "NVDA",
    "overall_risk_score": 0.4,
    "recommended_position_size": "5% of capital",
}

DEFAULT_ORDER = {
    "symbol": "NVDA",
    "order_type": "market",
    "quantity": 1,
    "input_mint": "SOL",
    "output_mint": "USDC",
    "amount": "1000",
}

DEFAULT_DECISION = {
    "ticker": "NVDA",
    "action": "BUY",
    "confidence": 0.7,
    "thesis": "Bullish",
    "reasoning": "Signals align",
    "order": DEFAULT_ORDER,
}


class FakeAgent:
    """Returns canned responses in call order; last response repeats."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.prompts = []

    def run(self, prompt):
        self.prompts.append(prompt)
        index = min(len(self.prompts) - 1, len(self.responses) - 1)
        return self.responses[index]


def make_agents(
    discovery='["NVDA", "MSFT"]',
    sentiment=None,
    decision=None,
):
    return {
        "director": FakeAgent(discovery, json.dumps(decision or DEFAULT_DECISION)),
        "sentiment": FakeAgent(
            sentiment
            if isinstance(sentiment, str)
            else json.dumps(sentiment or DEFAULT_SENTIMENT)
        ),
        "quant": FakeAgent(json.dumps(DEFAULT_QUANT)),
        "risk": FakeAgent(json.dumps(DEFAULT_RISK)),
        "execution": FakeAgent(json.dumps(DEFAULT_ORDER)),
    }


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _system(self, agents, **kwargs):
        return MarketMindAI(
            agents=agents,
            output_dir=self.temp_dir.name,
            output_type="dict",
            **kwargs,
        )

    def test_full_pipeline_produces_validated_stages(self):
        agents = make_agents()
        system = self._system(agents)
        output = system.run("Analyze NVDA and MSFT")

        self.assertEqual(output["tickers"], ["NVDA", "MSFT"])
        self.assertEqual(len(output["results"]), 2)
        first = output["results"][0]
        self.assertEqual(first["sentiment"]["ticker"], "NVDA")
        self.assertEqual(first["sentiment"]["overall_sentiment_score"], 0.8)
        self.assertEqual(first["quant"]["technical_score"], 0.7)
        self.assertEqual(first["risk"]["overall_risk_score"], 0.4)
        self.assertEqual(first["order"]["input_mint"], "SOL")
        self.assertEqual(first["decision"]["action"], "BUY")
        self.assertEqual(first["errors"], [])
        self.assertGreaterEqual(len(first["raw_outputs"]), 5)
        self.assertIsInstance(system.last_result, CycleResult)

        # Each stage receives the previous stage's validated output.
        self.assertIn("Bullish momentum", agents["quant"].prompts[0])
        self.assertIn("technical_score", agents["risk"].prompts[0])
        self.assertIn("overall_risk_score", agents["execution"].prompts[0])
        self.assertIn("Proposed order", agents["director"].prompts[1])
        self.assertIn("technical_score", agents["director"].prompts[1])

    def test_second_ticker_gets_its_own_typed_result(self):
        system = self._system(make_agents())
        output = system.run("Analyze NVDA and MSFT")
        second = output["results"][1]
        self.assertEqual(second["ticker"], "MSFT")
        self.assertEqual(second["sentiment"]["ticker"], "MSFT")
        self.assertEqual(second["decision"]["ticker"], "MSFT")

    def test_malformed_stage_does_not_abort_cycle(self):
        agents = make_agents(
            discovery='["NVDA"]', sentiment="I am unable to answer"
        )
        output = self._system(agents).run("Analyze NVDA")

        first = output["results"][0]
        self.assertIsNone(first["sentiment"])
        self.assertTrue(
            any("No valid JSON" in error for error in first["errors"])
        )
        self.assertEqual(first["decision"]["action"], "BUY")
        self.assertEqual(output["tickers"], ["NVDA"])

    def test_trading_is_disabled_by_default(self):
        output = self._system(make_agents()).run("Analyze NVDA")
        self.assertEqual(output["executions"], [])

    def test_dry_run_reports_simulated_execution(self):
        system = self._system(make_agents(), enable_trading=True, dry_run=True)
        output = system.run("Analyze NVDA and MSFT")
        self.assertEqual(
            [item["status"] for item in output["executions"]],
            ["SIMULATED", "SIMULATED"],
        )

    def test_live_execution_uses_jupiter_tools(self):
        get_order = Mock(
            return_value=json.dumps(
                {"transaction": "TX", "requestId": "REQ"}
            )
        )
        execute_trade = Mock(
            return_value=json.dumps({"status": "Success", "signature": "SIG"})
        )

        def load_tool(_module, name):
            return get_order if name == "get_order" else execute_trade

        system = self._system(
            make_agents(), enable_trading=True, dry_run=False
        )
        with patch(
            "market_mind_ai.tools.tools_registry.load_tool", side_effect=load_tool
        ):
            output = system.run("Analyze NVDA and MSFT")

        self.assertEqual(
            [item["status"] for item in output["executions"]],
            ["EXECUTED", "EXECUTED"],
        )
        get_order.assert_called_with("SOL", "USDC", "1000")
        execute_trade.assert_called_with("TX", "REQ")

    def test_hold_decision_is_never_submitted(self):
        decision = dict(DEFAULT_DECISION, action="HOLD")
        system = self._system(
            make_agents(decision=decision),
            enable_trading=True,
            dry_run=False,
        )
        with patch("market_mind_ai.tools.tools_registry.load_tool") as load_tool:
            output = system.run("Analyze NVDA")
        load_tool.assert_not_called()
        self.assertEqual(output["executions"], [])

    def test_unknown_action_is_normalized_to_hold(self):
        decision = dict(DEFAULT_DECISION, action="MAYBE")
        output = self._system(make_agents(decision=decision)).run("Analyze NVDA")
        first = output["results"][0]
        self.assertEqual(first["decision"]["action"], "HOLD")
        self.assertTrue(
            any("unknown action" in error for error in first["errors"])
        )

    def test_discovery_failure_is_recorded_not_fatal(self):
        output = self._system(make_agents(discovery="no tickers here")).run(
            "Analyze the market"
        )
        self.assertTrue(
            any("ticker_discovery" in error for error in output["errors"])
        )


if __name__ == "__main__":
    unittest.main()
