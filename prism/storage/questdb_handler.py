import sys
from datetime import datetime
from questdb.ingress import Sender, IngressError, TimestampNanos

class QuestDBHandler:
    """
    Handles data ingestion into QuestDB using InfluxDB Line Protocol (ILP).
    """
    def __init__(self, host: str = 'questdb', port: int = 9009):
        self.host = host
        self.port = port
        self.conf = f"http::addr={host}:{port};" # Using HTTP for simplicity if TCP fails, or TCP directly.
        # Actually, for Python client, standard is TCP usually. Let's use the standard TCP construction.
        # Conf string format: "tcp::addr=host:port;"
        self.conf = f"tcp::addr={host}:{port};"
        print(f"[{datetime.now()}] QuestDBHandler Initialized (Target: {host}:{port})")

    def insert_market_data(self, ticker: str, price: float, timestamp: datetime, source: str = 'tiingo'):
        """
        Inserts a single market data point.
        """
        try:
            with Sender.from_conf(self.conf) as sender:
                sender.row(
                    'market_data', # Table name
                    symbols={'symbol': ticker, 'source': source}, # Tags (indexed)
                    columns={'price': price}, # Fields
                    at=TimestampNanos.from_datetime(timestamp) # Designated Timestamp
                )
                sender.flush()
        except IngressError as e:
            print(f"[{datetime.now()}] QuestDB Ingestion Error: {e}")
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected Error inserting data: {e}")

    def insert_bulk_data(self, ticker: str, data_list: list, source: str = 'tiingo'):
        """
        Inserts a list of data points efficiently.
        Expects data_list to contain dicts with 'date'/'timestamp' and 'close'/'price'.
        Tiingo EOD format: {'date': '2023-01-01T00:00:00.000Z', 'close': 150.0, ...}
        """
        try:
            with Sender.from_conf(self.conf) as sender:
                for row in data_list:
                    # Handle different key names depending on endpoint (EOD vs IEX)
                    price = row.get('close') if 'close' in row else row.get('last')
                    
                    # Parse timestamp
                    ts_str = row.get('date') if 'date' in row else row.get('timestamp')
                    # Tiingo format often: 2019-01-02T00:00:00.000Z
                    # Python 3.11 fromisoformat handles 'Z' usually, but let's be safe
                    ts_str = ts_str.replace('Z', '+00:00') 
                    ts = datetime.fromisoformat(ts_str)

                    sender.row(
                        'market_data',
                        symbols={'symbol': ticker, 'source': source},
                        columns={'price': float(price), 'volume': float(row.get('volume', 0.0))},
                        at=TimestampNanos.from_datetime(ts)
                    )
                sender.flush()
            print(f"[{datetime.now()}] Successfully inserted {len(data_list)} rows for {ticker}.")
        except Exception as e:
            print(f"[{datetime.now()}] Error in bulk insert: {e}")
