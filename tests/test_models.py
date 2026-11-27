import unittest

from market_mind_ai.models import (
    QuantAnalysis,
    SentimentAnalysis,
    parse_model,
    parse_ticker_list,
)


class ParseModelTests(unittest.TestCase):
    def test_plain_json(self):
        model, error = parse_model(
            '{"ticker": "NVDA", "overall_sentiment_score": 0.8}',
            SentimentAnalysis,
        )
        self.assertIsNone(error)
        self.assertEqual(model.ticker, "NVDA")
        self.assertEqual(model.overall_sentiment_score, 0.8)

    def test_markdown_fence_and_prose(self):
        raw = (
            "Here is the analysis:\n```json\n"
            '{"ticker": "AAPL", "technical_score": 0.65}\n'
            "```\nHope this helps."
        )
        model, error = parse_model(raw, QuantAnalysis)
        self.assertIsNone(error)
        self.assertEqual(model.ticker, "AAPL")
        self.assertEqual(model.technical_score, 0.65)

    def test_defaults_fill_missing_ticker(self):
        model, error = parse_model(
            '{"overall_sentiment_score": 0.5}',
            SentimentAnalysis,
            defaults={"ticker": "MSFT"},
        )
        self.assertIsNone(error)
        self.assertEqual(model.ticker, "MSFT")

    def test_agent_value_wins_over_default(self):
        model, _ = parse_model(
            '{"ticker": "GOOG"}',
            SentimentAnalysis,
            defaults={"ticker": "MSFT"},
        )
        self.assertEqual(model.ticker, "GOOG")

    def test_invalid_score_is_rejected(self):
        model, error = parse_model(
            '{"ticker": "X", "overall_sentiment_score": 4}',
            SentimentAnalysis,
        )
        self.assertIsNone(model)
        self.assertIsNotNone(error)

    def test_non_json_returns_error_without_raising(self):
        model, error = parse_model("I cannot answer that", SentimentAnalysis)
        self.assertIsNone(model)
        self.assertIn("No valid JSON", error)

    def test_list_wrapper_uses_first_object(self):
        model, error = parse_model(
            '[{"ticker": "TSLA", "volume_score": 0.3}]', QuantAnalysis
        )
        self.assertIsNone(error)
        self.assertEqual(model.ticker, "TSLA")


class ParseTickerListTests(unittest.TestCase):
    def test_json_array(self):
        tickers, error = parse_ticker_list('["NVDA", "MSFT", "NVDA"]')
        self.assertIsNone(error)
        self.assertEqual(tickers, ["NVDA", "MSFT"])

    def test_keyed_object(self):
        tickers, _ = parse_ticker_list('{"tickers": ["AAPL", "GOOG"]}')
        self.assertEqual(tickers, ["AAPL", "GOOG"])

    def test_prose_fallback(self):
        tickers, _ = parse_ticker_list(
            "The relevant stocks are NVDA and MSFT for this task."
        )
        self.assertIn("NVDA", tickers)
        self.assertIn("MSFT", tickers)

    def test_empty_output(self):
        tickers, error = parse_ticker_list("")
        self.assertEqual(tickers, [])
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()
