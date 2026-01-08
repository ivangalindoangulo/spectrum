from strategies.interface import StrategyInterface

class TrendFollowing(StrategyInterface):
    def __init__(self, window_size=20):
        self._name = f"TrendFollowing_SMA{window_size}"
        self.window_size = window_size

    @property
    def name(self) -> str:
        return self._name

    def analyze(self, market_state: dict) -> dict:
        price = market_state.get('price')
        sma = market_state.get('sma')
        
        if not price or not sma:
            return {
                "signal": "HOLD",
                "confidence": 0.0,
                "metadata": {"reason": "Insufficient data"}
            }

        signal = "HOLD"
        confidence = 0.0
        
        if price > sma:
            signal = "BUY"
            confidence = 0.8
        elif price < sma:
            signal = "SELL"
            confidence = 0.8
            
        return {
            "signal": signal,
            "confidence": confidence,
            "metadata": {
                "price": price,
                "sma": sma,
                "strategy": self.name
            }
        }
