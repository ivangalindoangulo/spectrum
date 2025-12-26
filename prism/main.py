import threading
import time
import sys
from ingestion.service import IngestionService
from strategies.trend_following import TrendFollowing
from engine.runner import StrategyEngine

from utils.config import Config

def run_ingestion(tickers, source='tiingo'):
    # Runs the ingestion loop
    service = IngestionService(tickers, source=source)
    # Start with backfill (optional, maybe controlled by env var)
    try:
        service.run_backfill(Config.BACKFILL_START_DATE)
    except Exception as e:
        print(f"Backfill missing or failed: {e}")
        
    service.run_live_ingestion()

def run_strategy(ticker):
    # Runs the strategy engine
    # Give ingestion a moment to start
    time.sleep(5) 
    strategy = TrendFollowing(ticker, window=5)
    engine = StrategyEngine(strategy)
    engine.run()

def main():
    Config.print_config()
    
    ticker = Config.TARGET_TICKER
    source = Config.DATA_SOURCE
    
    # We use threads to simulate the microservices running together in this single container.
    # In a full production scale, these would be separate containers/deployments.
    
    # 1. Ingestion Thread
    ingest_thread = threading.Thread(target=run_ingestion, args=([ticker], source), daemon=True)
    ingest_thread.start()
    
    # 2. Strategy Engine Thread
    strategy_thread = threading.Thread(target=run_strategy, args=(ticker,), daemon=True)
    strategy_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping services...")
        sys.exit(0)

if __name__ == "__main__":
    main()
