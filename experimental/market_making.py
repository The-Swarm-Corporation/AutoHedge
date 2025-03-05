import asyncio
import csv
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import math
import os
import random
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import numpy as np
import pandas as pd
from loguru import logger
import websockets

# Market Making Strategy Configuration
@dataclass
class MarketMakingConfig:
    """Configuration for market making strategy."""
    trading_pair: str = 'BTC/USDT'  # Default trading pair
    total_capital: float = 10000.0  # Total capital to allocate
    spread_percentage: float = 0.001  # 0.1% spread
    order_size_percentage: float = 0.01  # 1% of total capital per order
    max_inventory_exposure: float = 0.2  # Max 20% of total capital in one asset
    rebalance_threshold: float = 0.1  # 10% deviation triggers rebalance
    min_profit_threshold: float = 0.002  # 0.2% minimum profit target

@dataclass
class MarketData:
    """Holds real-time market data for a trading pair."""
    timestamp: float = field(default_factory=time.time)
    best_bid: float = 0.0
    best_ask: float = 0.0
    last_price: float = 0.0
    volume: float = 0.0

class MarketMaker:
    """Advanced Market Making Algorithm for Crypto Trading."""
    
    def __init__(self, config: MarketMakingConfig):
        """
        Initialize the market maker with given configuration.
        
        Args:
            config (MarketMakingConfig): Configuration for market making strategy
        """
        self.config = config
        self.market_data = MarketData()
        
        # Logging setup
        logger.add("market_maker.log", rotation="10 MB")
        
        # Trading state tracking
        self.current_inventory = {
            'base': 0.0,  # e.g., BTC amount
            'quote': config.total_capital  # e.g., USDT amount
        }
        
        # Order tracking
        self.active_orders: Dict[str, Dict] = {}
        
        # CSV logging setup
        self.csv_filename = f"market_making_{config.trading_pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.initialize_csv_log()
    
    def initialize_csv_log(self):
        """Initialize CSV log with headers."""
        with open(self.csv_filename, 'w', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'event_type', 'price', 'amount', 
                'base_inventory', 'quote_inventory', 'total_value'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    async def fetch_market_data(self) -> MarketData:
        """
        Fetch real-time market data from multiple free sources.
        
        Returns:
            MarketData: Current market data snapshot
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Coinbase public ticker (free, no API key)
                async with session.get(f"https://api.coinbase.com/v2/prices/{self.config.trading_pair.replace('/', '-')}/spot") as response:
                    if response.status == 200:
                        data = await response.json()
                        last_price = float(data['data']['amount'])
                        
                        # Simulating bid/ask spread
                        spread = last_price * self.config.spread_percentage
                        
                        return MarketData(
                            timestamp=time.time(),
                            best_bid=last_price - spread/2,
                            best_ask=last_price + spread/2,
                            last_price=last_price,
                            volume=0.0  # Coinbase API doesn't provide volume in free tier
                        )
                    
            except Exception as e:
                logger.error(f"Market data fetch error: {e}")
                
                # Fallback to alternative free source if first fails
                try:
                    async with session.get(f"https://api.binance.com/api/v3/ticker/price?symbol={self.config.trading_pair.replace('/', '')}") as response:
                        if response.status == 200:
                            data = await response.json()
                            last_price = float(data['price'])
                            
                            spread = last_price * self.config.spread_percentage
                            
                            return MarketData(
                                timestamp=time.time(),
                                best_bid=last_price - spread/2,
                                best_ask=last_price + spread/2,
                                last_price=last_price,
                                volume=0.0
                            )
                except Exception as inner_e:
                    logger.error(f"Backup market data fetch error: {inner_e}")
                    
                    # Completely fallback to a simulated market data
                    return MarketData(
                        timestamp=time.time(),
                        best_bid=50000.0,
                        best_ask=50100.0,
                        last_price=50050.0,
                        volume=100.0
                    )
    
    def calculate_order_size(self) -> float:
        """
        Calculate appropriate order size based on current strategy and inventory.
        
        Returns:
            float: Order size in base asset
        """
        total_value = (
            self.current_inventory['base'] * self.market_data.last_price + 
            self.current_inventory['quote']
        )
        
        order_size = (
            self.config.total_capital * 
            self.config.order_size_percentage / 
            self.market_data.last_price
        )
        
        # Risk management: Ensure order size doesn't exceed max inventory exposure
        max_order_size = (
            self.config.total_capital * 
            self.config.max_inventory_exposure / 
            self.market_data.last_price
        )
        
        return min(order_size, max_order_size)
    
    def simulate_order(self, order_type: str, price: float, amount: float) -> Dict:
        """
        Simulate an order execution without actual trading.
        
        Args:
            order_type (str): 'buy' or 'sell'
            price (float): Order price
            amount (float): Order amount
        
        Returns:
            Dict: Simulated order details
        """
        order_id = f"sim_{int(time.time() * 1000)}"
        
        if order_type == 'buy':
            # Simulate buying
            if self.current_inventory['quote'] >= price * amount:
                self.current_inventory['base'] += amount
                self.current_inventory['quote'] -= price * amount
                logger.info(f"Simulated BUY: {amount} @ {price}")
            else:
                logger.warning("Insufficient funds for buy order")
                return {}
        
        elif order_type == 'sell':
            # Simulate selling
            if self.current_inventory['base'] >= amount:
                self.current_inventory['base'] -= amount
                self.current_inventory['quote'] += price * amount
                logger.info(f"Simulated SELL: {amount} @ {price}")
            else:
                logger.warning("Insufficient base asset for sell order")
                return {}
        
        # Log to CSV
        with open(self.csv_filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[
                'timestamp', 'event_type', 'price', 'amount', 
                'base_inventory', 'quote_inventory', 'total_value'
            ])
            writer.writerow({
                'timestamp': time.time(),
                'event_type': order_type.upper(),
                'price': price,
                'amount': amount,
                'base_inventory': self.current_inventory['base'],
                'quote_inventory': self.current_inventory['quote'],
                'total_value': (self.current_inventory['base'] * price + self.current_inventory['quote'])
            })
        
        return {
            'order_id': order_id,
            'type': order_type,
            'price': price,
            'amount': amount,
            'status': 'filled'
        }
    
    async def market_making_strategy(self):
        """
        Core market making strategy implementation.
        Continuously fetches market data and places orders.
        """
        while True:
            try:
                # Fetch latest market data
                self.market_data = await self.fetch_market_data()
                
                # Calculate order parameters
                order_size = self.calculate_order_size()
                
                # Place buy order slightly below market
                buy_price = self.market_data.best_bid * (1 - self.config.spread_percentage/2)
                self.simulate_order('buy', buy_price, order_size)
                
                # Place sell order slightly above market
                sell_price = self.market_data.best_ask * (1 + self.config.spread_percentage/2)
                self.simulate_order('sell', sell_price, order_size)
                
                # Wait before next iteration
                await asyncio.sleep(5)  # Adjust based on desired trading frequency
                
            except Exception as e:
                logger.error(f"Market making strategy error: {e}")
                await asyncio.sleep(10)  # Pause on error
    
    async def run(self):
        """
        Main execution method to start market making process.
        """
        logger.info(f"Starting Market Making for {self.config.trading_pair}")
        await self.market_making_strategy()

def main():
    """
    Main entry point for the market making algorithm.
    Allows configuration of trading pairs and capital.
    """
    # Example configurations
    configs = [
        MarketMakingConfig(trading_pair='BTC/USDT', total_capital=10000.0),
        MarketMakingConfig(trading_pair='ETH/USDT', total_capital=5000.0)
    ]
    
    async def run_market_makers():
        market_makers = [MarketMaker(config) for config in configs]
        await asyncio.gather(*[mm.run() for mm in market_makers])
    
    asyncio.run(run_market_makers())

if __name__ == "__main__":
    main()

# Backtest Evaluation Script
def backtest_market_maker(historical_data_path: str, config: MarketMakingConfig):
    """
    Backtest the market making strategy on historical data.
    
    Args:
        historical_data_path (str): Path to CSV with historical price data
        config (MarketMakingConfig): Market making configuration
    
    Returns:
        Dict: Performance metrics
    """
    # Load historical data
    df = pd.read_csv(historical_data_path)
    
    # Initialize backtest state
    initial_capital = config.total_capital
    current_inventory = {
        'base': 0.0,
        'quote': initial_capital
    }
    
    # Tracking variables
    trades = []
    
    # Simulate strategy
    for _, row in df.iterrows():
        current_price = row['close']
        
        # Market making logic (simplified)
        spread = current_price * config.spread_percentage
        buy_price = current_price - spread/2
        sell_price = current_price + spread/2
        
        order_size = (initial_capital * config.order_size_percentage) / current_price
        
        # Simulate buy
        if current_inventory['quote'] >= buy_price * order_size:
            current_inventory['base'] += order_size
            current_inventory['quote'] -= buy_price * order_size
            trades.append({
                'type': 'BUY',
                'price': buy_price,
                'amount': order_size
            })
        
        # Simulate sell
        if current_inventory['base'] >= order_size:
            current_inventory['base'] -= order_size
            current_inventory['quote'] += sell_price * order_size
            trades.append({
                'type': 'SELL',
                'price': sell_price,
                'amount': order_size
            })
    
    # Calculate performance
    final_value = (
        current_inventory['base'] * df.iloc[-1]['close'] + 
        current_inventory['quote']
    )
    
    return {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return_percentage': ((final_value - initial_capital) / initial_capital) * 100,
        'total_trades': len(trades)
    }

# Example usage for backtest
if __name__ == "__main__":
    # Assuming you have a historical price data CSV
    backtest_results = backtest_market_maker(
        'historical_prices.csv', 
        MarketMakingConfig(trading_pair='BTC/USDT')
    )
    print(json.dumps(backtest_results, indent=2))