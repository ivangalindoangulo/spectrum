import time
from datetime import datetime
from storage.questdb_handler import QuestDBHandler
# We need a way to query QuestDB. The Handler was for Ingestion (Sender).
# We need a SQL client.
import requests # We can use REST API for querying QuestDB

from utils.config import Config

class StrategyEngine:
    def __init__(self, strategy):
        self.strategy = strategy
        self.symbol = strategy.symbol
        # QuestDB REST API
        self.query_url = f"http://{Config.QUESTDB_HOST}:9000/exec" 

    def get_history(self, limit=100):
        """
        Selects recent history from QuestDB.
        """
        query = f"SELECT * FROM market WHERE ticker = '{self.symbol}' ORDER BY ts DESC LIMIT {limit}"
        try:
            r = requests.get(self.query_url, params={'query': query})
            if r.status_code == 200:
                data = r.json()
                # QuestDB returns {'columns': [...], 'dataset': [[...], [...]]}
                # We need to map it to list of dicts
                columns = [c['name'] for c in data['columns']]
                dataset = data['dataset']
                
                results = []
                # dataset is ordered DESC (latest first), so we should reverse it for warm-up
                for row in reversed(dataset):
                    record = dict(zip(columns, row))
                    results.append(record)
                return results
            else:
                print(f"Error querying history: {r.text}")
                return []
        except Exception as e:
            print(f"Engine DB Error: {e}")
            return []

    def get_latest(self):
        """
        Polls for the absolute latest record.
        """
        # Limiting to 1 gives the latest
        query = f"SELECT * FROM market WHERE ticker = '{self.symbol}' ORDER BY ts DESC LIMIT 1"
        try:
            r = requests.get(self.query_url, params={'query': query})
            if r.status_code == 200:
                data = r.json()
                if data['count'] > 0:
                    columns = [c['name'] for c in data['columns']]
                    row = data['dataset'][0]
                    return dict(zip(columns, row))
        except Exception as e:
            pass
        return None

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
                ts_str = latest.get('ts')
                # QuestDB REST returns ISO string usually: '2025-01-01T12:00:00.000000Z'
                # We need to parse it to check freshness
                try:
                    # Clean Z if present for fromisoformat
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    
                    # Check Freshness (e.g. is data from today/recent?)
                    # Current UTC time
                    now = datetime.now(ts.tzinfo) # Use timezone from ts if avail
                    diff = now - ts
                    
                    # If data is older than 1 hour, we assume backfill is still running or system is catching up
                    if diff.total_seconds() > 3600:
                        print(f"[{datetime.now()}] Engine: Syncing... Current DB Head: {ts}")
                        time.sleep(5)
                        continue
                        
                    # Process tick if new
                    if ts_str != last_timestamp:
                        print(f"Engine: processing {latest}")
                        price = latest.get('close')
                        self.strategy.on_tick(price, ts)
                        last_timestamp = ts_str
                except Exception as e:
                    print(f"Timestamp Parse Error: {e}")

            else:
               # No data returned (maybe table locked or empty)
               pass
            
            time.sleep(5) # Poll frequency
