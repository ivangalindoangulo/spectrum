import threading
import time
import sys
from ingestion.service import IngestionService
from engine.runner import AgentOrchestrator
from storage.timescale_handler import TimescaleHandler
from utils.config import Config

# Import Strategies
from strategies.trend.following import TrendFollowing

def run_ingestion(tickers, source='tiingo'):
    # Runs the ingestion loop
    service = IngestionService(tickers, source=source)
    # Start with backfill (optional, maybe controlled by env var)
    try:
        service.run_backfill(Config.BACKFILL_START_DATE)
    except Exception as e:
        print(f"Backfill missing or failed: {e}")
        
    service.run_live_ingestion()

def run_orchestrator(symbol, strategy_instance, db_handler):
    orchestrator = AgentOrchestrator(symbol, strategy_instance, db_handler)
    orchestrator.run()

def main():
    Config.print_config()
    
    ticker = Config.TARGET_TICKER # e.g. "BTCUSD"
    source = Config.DATA_SOURCE
    
    # Shared Database Handler (Thread Safe)
    db_handler = TimescaleHandler(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        dbname=Config.DB_NAME
    )
    
    # 1. Ingestion Thread (Data Producer)
    ingest_thread = threading.Thread(target=run_ingestion, args=([ticker], source), daemon=True)
    ingest_thread.start()
    
    # 2. Strategy Orchestrators (Data Consumers / Agents)
    
    # Strategy A: Trend Following on BTC
    trend_strategy = TrendFollowing(window_size=20)
    
    orch_a = threading.Thread(
        target=run_orchestrator, 
        args=(ticker, trend_strategy, db_handler), 
        daemon=True
    )
    orch_a.start()
    
    # Strategy B: Another instance or different strategy
    # For now, let's run a tighter Trend Strategy as "Simulated Scalping"
    scalp_strategy = TrendFollowing(window_size=5)
    scalp_strategy._name = "Scalping_V1" # Hacky rename for demo

    orch_b = threading.Thread(
        target=run_orchestrator,
        args=(ticker, scalp_strategy, db_handler),
        daemon=True
    )
    orch_b.start()

    
    print(f"[{time.ctime()}] System Running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping services...")
        sys.exit(0)

if __name__ == "__main__":
    main()

