from market_mind_ai import MarketMindAI  # loads .env from project root

# Initialize the trading system (tickers are derived from the task by the director)
trading_system = MarketMindAI(
    name="swarms-fund",
    description="Private Hedge Fund for Swarms Corp",
)

task = "Analyze the sentiment of oil market and provide a thesis on the overall market position and expected trends."
print(trading_system.run(task=task))
