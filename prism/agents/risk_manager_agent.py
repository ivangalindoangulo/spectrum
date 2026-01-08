from agents.agent_base import BaseAgent

class RiskManagerAgent(BaseAgent):
    """
    Responsibilities:
    1. Receive 'TradingSignal' from QuantAgent.
    2. Check global risk rules (Max position, Stop Loss limits, etc.).
    3. Approve, Reject, or Modify the signal.
    """
    def __init__(self, max_position_size=1.0):
        super().__init__("RiskManagerAgent")
        self.max_position_size = max_position_size

    def validate(self, signal: dict) -> dict:
        """
        Returns a RiskCheckResult dict.
        """
        action = signal.get('signal')
        
        if action == "HOLD":
            return {
                "approved": False,
                "adjusted_size": 0.0,
                "reason": "Signal was HOLD"
            }
            
        # Example Rule: Simulate acceptance
        # In real world, we would check current portfolio exposure here.
        
        approved = True
        reason = "Within limits"
        size = 0.1 # Default fixed lot size for now
        
        if size > self.max_position_size:
            approved = False
            reason = "Exceeds max position size"
            size = 0.0
            
        self.log(f"Evaluating {action} signal for {signal.get('symbol')}: {reason}")

        return {
            "signal_id": None, # Will be populated by Orchestrator after DB insert
            "approved": approved,
            "adjusted_size": size,
            "reason": reason
        }
