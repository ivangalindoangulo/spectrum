import time
import os
from datetime import datetime
from ingestion.tiingo_ingestor import TiingoProcessor
from ingestion.binance_ingestor import BinanceProcessor
from storage.questdb_handler import QuestDBHandler

from utils.config import Config

class IngestionService:
    def __init__(self, tickers: list, source: str = 'tiingo'):
        self.tickers = tickers
        self.source = source.lower()
        self.db = QuestDBHandler(host=Config.QUESTDB_HOST, port=Config.QUESTDB_PORT)
        
        if self.source == 'binance':
            self.processor = BinanceProcessor()
        else:
            self.processor = TiingoProcessor()
            
        print(f"[{datetime.now()}] Ingestion Service Initialized for {len(tickers)} tickers using {self.source}.")

    def run_backfill(self, start_date: str):
        """
        Backfills historical data. Checks latest DB timestamp to avoid re-downloading everything.
        """
        from utils.config import Config
        print(f"--- Starting Backfill ({self.source}) ---")
        
        for ticker in self.tickers:
            # 1. Check DB for last timestamp
            last_ts = self.db.get_latest_timestamp(ticker)
            
            # Determine effective start date
            if last_ts:
                print(f"[{datetime.now()}] Found existing data for {ticker}. Last entry: {last_ts}")
                # Start from the last timestamp found
                # Binance requires string format or int, convert datetime to string
                # We add a small buffer to avoid overlap if desired, but QuestDB handles dedup usually
                effective_start = last_ts.strftime("%d %b, %Y")
            else:
                print(f"[{datetime.now()}] No existing data for {ticker}. Starting full download from {start_date}.")
                effective_start = start_date

            # 2. Fetch History
            if self.source == 'binance':
                interval = Config.KLINE_INTERVAL
                print(f"[{datetime.now()}] Downloading history for {ticker} ({interval}) since {effective_start}...")
                # Binance processor handles the pagination logic
                history = self.processor.get_historical_data(ticker, interval=interval, start_str=effective_start)
            else:
                # Tiingo logic (simple daily usually)
                history = self.processor.get_historical_data(ticker, start_date=effective_start)
                
            # 3. Store
            if history:
                self.db.insert_bulk_data(ticker, history, source=self.source)
            else:
                print(f"[{datetime.now()}] Data is up to date.")
                
        print("--- Backfill Complete ---")

    def run_live_ingestion(self):
        """
        Continuous loop for fetching and inserting realtime data.
        """
        print(f"--- Starting Live Ingestion ({self.source}) ---")
        while True:
            for ticker in self.tickers:
                try:
                    data = self.processor.get_latest_price(ticker)
                    if data:
                        timestamp = datetime.now() # Default if not provided
                        price = 0.0

                        if self.source == 'binance':
                            # Binance format: {'symbol': 'BTCUSDT', 'price': '123.45'} checks
                            price = float(data.get('price', 0.0))
                            # Binance ticker endpoint doesn't always return a timestamp, so we use current server time
                        else:
                            # Tiingo format includes timestamp
                            price = data.get('last')
                            if 'timestamp' in data:
                                timestamp = datetime.fromisoformat(data['timestamp'])
                        
                        print(f"[{datetime.now()}] INGEST: {ticker} @ {price}")
                        self.db.insert_market_data(ticker, float(price), timestamp, source=self.source)
                except Exception as e:
                    print(f"Error ingest {ticker}: {e}")
            
            # Sleep logic
            time.sleep(10 if self.source == 'binance' else 60)

if __name__ == "__main__":
    # Example usage
    service = IngestionService(tickers=["BTCUSDT"], source='binance')
    service.run_backfill("1 Jan, 2024")
    service.run_live_ingestion()
    service.run_live_ingestion()
