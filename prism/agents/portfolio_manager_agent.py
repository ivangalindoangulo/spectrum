from agents.agent_base import BaseAgent

class PortfolioManagerAgent(BaseAgent):
    """
    Responsibilities:
    1. Receive approved 'RiskCheckResult'.
    2. Execute the order (Simulate or call Exchange API).
    3. Update local portfolio state.
    """
    def __init__(self):
        super().__init__("PortfolioManagerAgent")

    def execute(self, risk_check: dict, original_signal: dict) -> dict:
        """
        Executes the order and returns OrderResult.
        """
        if not risk_check.get('approved'):
            return {
                "status": "SKIPPED",
                "execution_price": 0.0,
                "filled_size": 0.0
            }
            
        symbol = original_signal.get('symbol')
        action = original_signal.get('signal')
        size = risk_check.get('adjusted_size')
        
        # Simulate Execution
        # In production this would call Binance Client
        market_price = float(original_signal.get('analysis', '{}').split('"price": ')[1].split(',')[0]) # Hacky parse or pass price better
        # Actually better to pass market_price in arguments or trust execution returns
        
        self.log(f"EXECUTING {action} {size} {symbol} ...")
        
        return {
            "status": "FILLED",
            "execution_price": 0.0, # Placeholder
            "filled_size": size
        }
