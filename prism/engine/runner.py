import time
from datetime import datetime, timezone
from storage.timescale_handler import TimescaleHandler
from utils.config import Config

class StrategyEngine:
    def __init__(self, strategy):
        self.strategy = strategy
        self.symbol = strategy.symbol
        
        self.db = TimescaleHandler(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dbname=Config.DB_NAME
        )

    def get_history(self, limit=100):
        """
        Selects recent history from DB.
        """
        results = self.db.get_history(self.symbol, limit=limit)
        # Runner expects chronological order for warm-up?
        # Original: "dataset is ordered DESC... so we should reverse it"
        # Handler returns DESC. So we reverse it here.
        return results[::-1]

    def get_latest(self):
        """
        Polls for the absolute latest record.
        """
        return self.db.get_latest(self.symbol)

    def run(self):
        print(f"--- Starting Strategy Engine for {self.symbol} ---")
        
        # 1. Wait for DB and Warm-up
        history = []
        while True:
            history = self.get_history(limit=50)
            if history:
                print(f"[{datetime.now()}] Engine: DB connection established using {len(history)} records.")
                break
            else:
                print(f"[{datetime.now()}] Engine: Waiting for market data to act available...")
                time.sleep(10)
        
        self.strategy.on_start(history)
        
        last_timestamp = None
        if history:
            # We assume 'ts' column exists
            last_timestamp = history[-1].get('ts')

        # 2. Main Loop
        while True:
            latest = self.get_latest()
            
            if latest:
                # ts should be datetime object from psycopg2
                ts = latest.get('ts')
                
                if not isinstance(ts, datetime):
                     # Fallback if somehow not datetime
                     try:
                        ts = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                     except:
                        pass

                # Check Freshness (e.g. is data from today/recent?)
                # Current UTC time
                now = datetime.now(timezone.utc)
                if ts.tzinfo is None:
                    # Assume UTC if naive
                    ts = ts.replace(tzinfo=timezone.utc)
                    
                diff = now - ts
                
                # If data is older than 1 hour, we assume backfill is still running or system is catching up
                if diff.total_seconds() > 3600:
                    print(f"[{datetime.now()}] Engine: Syncing... Current DB Head: {ts}")
                    time.sleep(5)
                    continue
                    
                # Process tick if new
                if ts != last_timestamp:
                    print(f"Engine: processing {latest.get('close')}")
                    price = latest.get('close')
                    self.strategy.on_tick(price, ts)
                    last_timestamp = ts
            else:
               # No data returned
               pass
            
            time.sleep(5) # Poll frequency
