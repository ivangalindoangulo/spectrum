from abc import ABC, abstractmethod
from datetime import datetime

class Strategy(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol
    
    @abstractmethod
    def on_start(self, historical_data):
        """
        Called when the strategy starts.
        historical_data: A DataFrame or list of dicts with past data for warm-up.
        """
        pass

    @abstractmethod
    def on_tick(self, price, timestamp):
        """
        Called on every new market tick.
        """
        pass
