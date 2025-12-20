import threading
import time
import sys
from ingestion.service import IngestionService
from strategies.trend_following import TrendFollowing
from engine.runner import StrategyEngine

def run_ingestion(tickers):
    # Runs the ingestion loop
    service = IngestionService(tickers)
    # Start with backfill (optional, maybe controlled by env var)
    try:
        service.run_backfill("2024-01-01")
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
    print("--------------------------------------------------")
    print("Spectrum - Prism Service (Hybrid Architecture)")
    print("--------------------------------------------------")
    
    ticker = "aapl"
    
    # We use threads to simulate the microservices running together in this single container.
    # In a full production scale, these would be separate containers/deployments.
    
    # 1. Ingestion Thread
    ingest_thread = threading.Thread(target=run_ingestion, args=([ticker],), daemon=True)
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
