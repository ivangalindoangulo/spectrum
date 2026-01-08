from agents.agent_base import BaseAgent
import pandas as pd

class MarketDataAgent(BaseAgent):
    """
    Responsibilities:
    1. Receive raw price updates.
    2. Maintain historical buffer.
    3. Compute technical indicators (SMA, RSI, etc.).
    4. Return a 'MarketState' object for the Quant Agent.
    """
    def __init__(self, window_size=20):
        super().__init__("MarketDataAgent")
        self.window_size = window_size
        self.history = []

    def warm_up(self, historical_data):
        """
        historical_data: List of dicts [{'close': 100, ...}]
        """
        self.log(f"Warming up with {len(historical_data)} records...")
        for row in historical_data:
            price = row.get('close')
            if price:
                self.history.append(float(price))
                if len(self.history) > self.window_size:
                    self.history.pop(0)

    def process_tick(self, price, timestamp) -> dict:
        """
        Updates state and returns calculated indicators.
        """
        self.history.append(float(price))
        if len(self.history) > self.window_size:
            self.history.pop(0)

        # Compute SMA
        sma = sum(self.history) / len(self.history) if self.history else 0
        
        return {
            "price": price,
            "timestamp": timestamp,
            "sma": sma,
            "history_len": len(self.history)
        }
