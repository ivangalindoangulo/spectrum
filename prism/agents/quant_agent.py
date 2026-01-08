from agents.agent_base import BaseAgent
from strategies.interface import StrategyInterface
import json

class QuantAgent(BaseAgent):
    """
    Responsibilities:
    1. Receive 'MarketState' from MarketDataAgent.
    2. Delegate analysis to the injected Strategy.
    3. Generate a 'TradingSignal'.
    """
    def __init__(self, symbol: str, strategy: StrategyInterface):
        super().__init__(f"QuantAgent-{strategy.name}")
        self.symbol = symbol
        self.strategy = strategy

    def analyze(self, market_state: dict) -> dict:
        """
        Returns a Signal dict.
        """
        # Delegate logic to the specific strategy
        result = self.strategy.analyze(market_state)
        
        signal = result.get('signal', 'HOLD')
        confidence = result.get('confidence', 0.0)
        metadata = result.get('metadata', {})

        # Return structured signal
        return {
            "strategy_id": self.strategy.name,
            "symbol": self.symbol,
            "signal": signal,
            "confidence": confidence,
            "analysis": json.dumps(metadata)
        }

