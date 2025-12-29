import time
import os
from datetime import datetime
from ingestion.tiingo_ingestor import TiingoProcessor
from ingestion.binance_ingestor import BinanceProcessor
from storage.questdb_handler import QuestDBHandler

from utils.config import Config

class IngestionService:
    def __init__(self, tickers: list, source: str):
        self.tickers = tickers
        self.source = source.lower()
        self.db = QuestDBHandler(host=Config.QUESTDB_HOST, port=Config.QUESTDB_PORT)
        
        if self.source == 'binance':
            self.processor = BinanceProcessor()
        else:
            self.processor = TiingoProcessor()
            
        print(f"[{datetime.now()}] Ingestion Service Initialized for {len(tickers)} tickers using {self.source}.")

    def close(self):
        """Cleanup resources."""
        if self.db:
            self.db.close()
            print(f"[{datetime.now()}] Ingestion Service closed.")

    def run_backfill(self, start_date: str):
        """
        Backfills historical data. Checks latest DB timestamp to avoid re-downloading everything.
        Uses chunking to handle large datasets robustly.
        """
        from utils.config import Config
        import pandas as pd
        from datetime import timedelta
        
        print(f"--- Starting Backfill ({self.source}) ---")
        
        for ticker in self.tickers:
            # 1. Determine Start Date
            last_ts = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    last_ts = self.db.get_latest_timestamp(ticker)
                    break 
                except Exception as e:
                    print(f"[{datetime.now()}] Warning: DB Query failed (Attempt {attempt+1}/{max_retries}): {e}")
                    time.sleep(2)
            
            # If still failing after retries, we shouldn't assume empty. We should probably stop to check DB health.
            # But for now, if it raised exception all 3 times, let's assume CRITICAL error and raise it up.
            # Or if it returned None (valid empty), we proceed.
            # The previous code raised exception on error, returned None on empty.
            # So if we are here and didn't break, it means we exhausted retries with exceptions.
            # Wait, the logic above breaks on success (including None return if no exception).
            # So if we finish the loop without break, it's an error.
            else:
                 print(f"[{datetime.now()}] CRITICAL: Could not query DB for {ticker} history. Aborting backfill for this ticker.")
                 continue

            if last_ts:
                # Add 1 min to avoid overlap
                start_dt = last_ts + timedelta(minutes=1)
                print(f"[{datetime.now()}] Found existing data for {ticker}. Resuming form: {start_dt}")
            else:
                # Parse config start string
                try:
                    start_dt = pd.to_datetime(start_date).to_pydatetime()
                except:
                    # Fallback
                    start_dt = datetime.strptime(start_date, "%d %b, %Y")
                
                print(f"[{datetime.now()}] No existing data for {ticker}. Starting full download from {start_dt}.")

            # 2. Loop in Chunks (e.g. 15 days) to ensure stability
            # 15 days * 1440 mins = 21,600 rows. Very safe.
            from datetime import timezone
            
            # Ensure start_dt has timezone info if it doesn't, assuming UTC
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            
            # Use current UTC time for 'now'
            now = datetime.now(timezone.utc)
            
            chunk_size = timedelta(days=15)
            
            current_start = start_dt
            
            while current_start < now:
                current_end = min(current_start + chunk_size, now)
                
                # Format for Binance (usually accepts strings like "1 Jan, 2020")
                # We can also pass timestamps if supported, but string is safest with python-binance wrapper
                s_str = current_start.strftime("%d %b, %Y %H:%M:%S")
                e_str = current_end.strftime("%d %b, %Y %H:%M:%S")
                
                if self.source == 'binance':
                    interval = Config.KLINE_INTERVAL
                    print(f"[{datetime.now()}] Downloading chunk {s_str} -> {e_str}...")
                    try:
                        history = self.processor.get_historical_data(ticker, interval=interval, start_str=s_str, end_str=e_str)
                        if history:
                            self.db.insert_bulk_data(ticker, history, source=self.source, interval=interval)
                            print(f"   -> Inserted {len(history)} records.")
                        else:
                            print("   -> No data in this chunk (gap?).")
                    except Exception as e:
                         print(f"   -> Error in chunk: {e}")
                else:
                    # Tiingo (keep simple for now, usually daily)
                    # Tiingo logic...
                    history = self.processor.get_historical_data(ticker, start_date=s_str)
                    if history:
                        self.db.insert_bulk_data(ticker, history, source=self.source)
                        
                # Move forward
                current_start = current_end
                time.sleep(0.5) # Rate limit politeness

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
                        timestamp = datetime.now(timezone.utc) # Default if not provided
                        price = 0.0

                        if self.source == 'binance':
                            price = float(data.get('price', 0.0))
                        else:
                            price = data.get('last')
                            if 'timestamp' in data:
                                timestamp = datetime.fromisoformat(data['timestamp'])
                        
                        print(f"[{datetime.now()}] INGEST: {ticker} @ {price}")
                        self.db.insert_market_data(ticker, float(price), timestamp, source=self.source, interval=Config.KLINE_INTERVAL)
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
