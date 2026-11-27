from market_mind_ai.env_loader import load_env

load_env()

from market_mind_ai.main import MarketMindAI  # noqa: E402  (env must load first)

# Backwards-compatible alias for the previous package name.
AutoHedge = MarketMindAI

__all__ = ["MarketMindAI", "AutoHedge"]
