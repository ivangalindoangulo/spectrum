from abc import ABC, abstractmethod

class StrategyInterface(ABC):
    """
    Interface that all trading strategies must implement.
    Decoupled from the QuantAgent infrastructure.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def analyze(self, market_state: dict) -> dict:
        """
        Analyzes the market state and returns a signal.
        
        Args:
            market_state: Dict containing 'price', 'sma', 'history', etc.
            
        Returns:
            Dict with keys: 'signal' (BUY/SELL/HOLD), 'confidence' (0.0-1.0), 'metadata' (dict)
        """
        pass
