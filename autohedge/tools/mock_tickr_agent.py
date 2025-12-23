from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class IndividualTickrAgentOutput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    market_data: Optional[str] = Field(None, description="Mock market data for the stock")

class MockTickrAgent:
    """
    A mock implementation of the TickrAgent to bypass issues with the external package.
    It returns dummy market data.
    """
    def __init__(self, stocks: List[str], **kwargs):
        self.stocks = stocks
        print(f"MockTickrAgent initialized for stocks: {stocks}")

    def run(self, task: str) -> List[IndividualTickrAgentOutput]:
        print(f"MockTickrAgent running task: '{task}'")
        results = []
        for stock in self.stocks:
            mock_data = f"Mock market data for {stock}: current_price=150.0, volume=1000000, pe_ratio=25.5. This is simulated data."
            results.append(IndividualTickrAgentOutput(ticker=stock, market_data=mock_data))
        return results

# This mock will be imported by autohedge/main.py temporarily
# The original TickrAgent also had other parameters like max_loops, workers, retry_attempts, context_length
# This mock simplifies that.
