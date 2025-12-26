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
        query = f"SELECT * FROM market WHERE symbol = '{self.symbol}' ORDER BY timestamp DESC LIMIT {limit}"
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
        query = f"SELECT * FROM market WHERE symbol = '{self.symbol}' ORDER BY timestamp DESC LIMIT 1"
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
        
        # 1. Warm-up
        history = self.get_history(limit=50)
        self.strategy.on_start(history)
        
        last_timestamp = None
        if history:
            # We assume 'timestamp' column exists. In QuestDB ILP it's the designated timestamp.
            # Usually strict name is 'timestamp' but ILP might name it 'timestamp' if we configured it,
            # or it is the default designated timestamp column. QuestDB default designated ts is 'timestamp'.
            last_timestamp = history[-1].get('timestamp')

        # 2. Main Loop
        while True:
            latest = self.get_latest()
            print(f"Engine: processing {latest}")
            if latest:
                ts = latest.get('timestamp')
                # Only process if it's new
                if ts != last_timestamp:
                    price = latest.get('price')
                    self.strategy.on_tick(price, ts)
                    last_timestamp = ts
                else:
                    # No new data
                    pass
            
            time.sleep(5) # Poll frequency
