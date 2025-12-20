import time
import os
from datetime import datetime
from ingestion.tiingo_ingestor import TiingoProcessor
from storage.questdb_handler import QuestDBHandler

class IngestionService:
    def __init__(self, tickers: list):
        self.tickers = tickers
        self.tiingo = TiingoProcessor()
        self.db = QuestDBHandler()
        print(f"[{datetime.now()}] Ingestion Service Initialized for {len(tickers)} tickers.")

    def run_backfill(self, start_date: str):
        """
        Backfills historical data for all tickers.
        """
        print("--- Starting Backfill ---")
        for ticker in self.tickers:
            history = self.tiingo.get_historical_data(ticker, start_date=start_date)
            if history:
                self.db.insert_bulk_data(ticker, history)
        print("--- Backfill Complete ---")

    def run_live_ingestion(self):
        """
        Continuous loop for fetching and inserting realtime data.
        """
        print("--- Starting Live Ingestion ---")
        while True:
            for ticker in self.tickers:
                try:
                    data = self.tiingo.get_latest_price(ticker)
                    if data:
                        price = data.get('last')
                        # Tiingo IEX timestamp usually is UTC ISO8601
                        timestamp_str = data.get('timestamp')
                        timestamp = datetime.fromisoformat(timestamp_str)
                        
                        print(f"[{datetime.now()}] INGEST: {ticker} @ {price}")
                        self.db.insert_market_data(ticker, float(price), timestamp)
                except Exception as e:
                    print(f"Error ingest {ticker}: {e}")
            
            # Rate limit guard (48 calls/hr per ticker roughly if 1 ticker)
            # If multiple tickers, we need to adjust wait time to share the quota 
            # or just rely on 429 handling.
            # For this demo, we assume 1 ticker and wait 75s.
            time.sleep(75)

if __name__ == "__main__":
    # Can be run standalone
    service = IngestionService(tickers=["aapl"])
    service.run_backfill("2024-01-01")
    service.run_live_ingestion()
