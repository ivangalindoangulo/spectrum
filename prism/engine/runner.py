import time
import threading
from datetime import datetime, timezone
import json

from storage.timescale_handler import TimescaleHandler
from utils.config import Config

# Import Agents
from agents.market_data_agent import MarketDataAgent
from agents.quant_agent import QuantAgent
from agents.risk_manager_agent import RiskManagerAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent

from strategies.interface import StrategyInterface

class AgentOrchestrator:
    """
    Coordinator that drives the AI Hedge Fund pipeline:
    Market Data -> Quant -> Risk -> Portfolio
    
    It runs in its own thread for a specific symbol/strategy pair.
    """
    def __init__(self, symbol: str, strategy: StrategyInterface, db_handler: TimescaleHandler):
        self.symbol = symbol
        self.strategy = strategy
        self.db = db_handler
        self.stop_requested = False
        
        # Initialize Agents
        self.market_agent = MarketDataAgent()
        self.quant_agent = QuantAgent(symbol, strategy) # Inject Strategy
        self.risk_agent = RiskManagerAgent()
        self.portfolio_agent = PortfolioManagerAgent()
        
        print(f"[{datetime.now()}] Orchestrator initialized for {symbol} ({strategy.name})")


    def run(self):
        """
        Main execution loop.
        """
        print(f"--- Starting Orchestrator for {self.symbol} ---")
        
        # 1. Warm-up
        history = self._fetch_history_for_warmup()
        self.market_agent.warm_up(history)
        
        last_timestamp = None
        if history:
             last_timestamp = history[-1].get('ts')

        # 2. Main Loop
        while not self.stop_requested:
            try:
                latest = self.db.get_latest(self.symbol)
                
                if latest:
                    ts = latest.get('ts')
                    # Ensure timezone aware
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                        
                    # Process only if new tick
                    if ts != last_timestamp:
                        price = latest.get('close')
                        self.process_pipeline(price, ts)
                        last_timestamp = ts
                        
            except Exception as e:
                print(f"Error in orchestrator loop {self.symbol}: {e}")
                
            time.sleep(1) # Poll frequency

    def process_pipeline(self, price, timestamp):
        """
        Executes one full cycle of the agent pipeline.
        """
        # Step 1: Market Data Agent
        market_state = self.market_agent.process_tick(price, timestamp)
        
        # Step 2: Quant Agent (Generate Signal)
        signal = self.quant_agent.analyze(market_state)
        
        # Traceability: Record Signal
        signal_id = self.db.record_signal(
            strategy_id=signal['strategy_id'],
            ticker=signal['symbol'],
            signal=signal['signal'],
            confidence=signal['confidence'],
            analysis_json=signal['analysis']
        )
        
        if signal['signal'] == "HOLD":
            return # No action needed

        # Step 3: Risk Manager Agent (Validate)
        risk_check = self.risk_agent.validate(signal)
        
        # Traceability: Record Risk Check
        risk_check_id = self.db.record_risk_check(
            signal_id=signal_id,
            approved=risk_check['approved'],
            adjusted_size=risk_check['adjusted_size'],
            reason=risk_check['reason']
        )
        
        # Step 4: Portfolio Manager Agent (Execute)
        if risk_check['approved']:
            order_result = self.portfolio_agent.execute(risk_check, signal)
            
            # Traceability: Record Order
            self.db.record_order(
                risk_check_id=risk_check_id,
                status=order_result['status'],
                execution_price=price 
            )

    def _fetch_history_for_warmup(self):
        # Helper to get data from DB
        raw = self.db.get_history(self.symbol, limit=50)
        return raw[::-1] # Reverse to chrono order

    def stop(self):
        self.stop_requested = True

