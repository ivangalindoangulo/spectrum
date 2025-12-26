import requests
import json
from datetime import datetime
from questdb.ingress import Sender, IngressError, TimestampNanos

class QuestDBHandler:
    # ... (existing init) ...
    def __init__(self, host: str = 'questdb', port: int = 9009, query_port: int = 9000):
        self.host = host
        self.port = port
        self.query_url = f"http://{host}:{query_port}/exec"
        self.conf = f"tcp::addr={host}:{port};"
        print(f"[{datetime.now()}] QuestDBHandler Initialized (Ingest: {port}, Query: {query_port})")

    # ... (existing insertion methods) ...

    def insert_market_data(self, ticker: str, price: float, timestamp: datetime, source: str = 'tiingo'):
        """
        Inserts a single market data point.
        """
        try:
            with Sender.from_conf(self.conf) as sender:
                sender.row(
                    'market', # Table name
                    symbols={'symbol': ticker, 'source': source}, # Tags (indexed)
                    columns={'price': price}, # Fields
                    at=TimestampNanos.from_datetime(timestamp) # Designated Timestamp
                )
                sender.flush()
        except IngressError as e:
            print(f"[{datetime.now()}] QuestDB Ingestion Error: {e}")
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected Error inserting data: {e}")

    def get_latest_timestamp(self, ticker: str):
        """
        Queries DB to find the last recorded timestamp for a symbol.
        """
        try:
            query = f"SELECT max(timestamp) FROM market WHERE symbol = '{ticker}'"
            response = requests.get(self.query_url, params={'query': query})
            
            if response.status_code == 200:
                data = response.json()
                if data['dataset'] and data['dataset'][0][0]:
                    # QuestDB returns format like '2023-12-25T12:00:00.000000Z'
                    ts_str = data['dataset'][0][0]
                    # Clean/parse to datetime
                    # Python usually handles the ISO format well
                    return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            return None
        except Exception as e:
            print(f"[{datetime.now()}] Error querying latest timestamp: {e}")
            return None

    def insert_bulk_data(self, ticker: str, data_list: list, source: str = 'tiingo'):
        # ... (rest of the method as before) ...
        try:
            with Sender.from_conf(self.conf) as sender:
                for row in data_list:
                    # Parse timestamp
                    ts_val = row.get('date') if 'date' in row else row.get('timestamp')
                    
                    if isinstance(ts_val, (int, float)):
                        if ts_val > 100000000000:
                            ts = datetime.fromtimestamp(ts_val / 1000.0)
                        else:
                            ts = datetime.fromtimestamp(ts_val)
                    else:
                        ts_str = str(ts_val).replace('Z', '+00:00')
                        ts = datetime.fromisoformat(ts_str)

                    # Construir columnas dinámicamente según los datos disponibles
                    columns = {}
                    
                    # Si es data completa OHLCV (común en backfill)
                    if 'open' in row and 'close' in row:
                        columns['open'] = float(row['open'])
                        columns['high'] = float(row['high'])
                        columns['low'] = float(row['low'])
                        columns['close'] = float(row['close'])
                        columns['price'] = float(row['close']) 
                    else:
                        p = row.get('close') if 'close' in row else row.get('last')
                        if p is not None:
                            columns['price'] = float(p)

                    if 'volume' in row:
                        columns['volume'] = float(row['volume'])

                    sender.row(
                        'market',
                        symbols={'symbol': ticker, 'source': source},
                        columns=columns,
                        at=TimestampNanos.from_datetime(ts)
                    )
                sender.flush()
            print(f"[{datetime.now()}] Successfully inserted {len(data_list)} rows for {ticker}.")
        except Exception as e:
            print(f"[{datetime.now()}] Error in bulk insert: {e}")
