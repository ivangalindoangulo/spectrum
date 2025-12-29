import requests
import json
from datetime import datetime, timezone
from questdb.ingress import Sender, IngressError, TimestampNanos

class QuestDBHandler:
    def __init__(self, host: str = 'questdb', port: int = 9009, query_port: int = 9000):
        self.host = host
        self.port = port
        self.query_url = f"http://{host}:{query_port}/exec"
        self.conf = f"tcp::addr={host}:{port};"
        print(f"[{datetime.now()}] QuestDBHandler Initialized (Ingest: {port}, Query: {query_port})")
        
        self.sender = None
        self.session = requests.Session()
        self.connect()

    def connect(self):
        """Initializes the persistent sender connection."""
        try:
            if self.sender:
                self.sender.close()
            
            # Create a new sender instance
            self.sender = Sender.from_conf(self.conf)
            # self.sender.connect() # removed, not needed or invalid in this version
            print(f"[{datetime.now()}] QuestDB Sender connected.")
        except Exception as e:
            print(f"[{datetime.now()}] Failed to connect QuestDB Sender: {e}")
            self.sender = None

    def close(self):
        """Closes the persistent sender connection and HTTP session."""
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                print(f"[{datetime.now()}] Error closing HTTP session: {e}")
        
        if self.sender:
            try:
                self.sender.flush()
                self.sender.close()
                print(f"[{datetime.now()}] QuestDB Sender closed.")
            except Exception as e:
                print(f"[{datetime.now()}] Error closing QuestDB Sender: {e}")
            finally:
                self.sender = None

    def insert_market_data(self, ticker: str, price: float, timestamp: datetime, source: str, interval: str = '1m'):
        """
        Inserts a single market data point using the persistent sender.
        """
        if not self.sender:
            self.connect()
            if not self.sender:
                print(f"[{datetime.now()}] Error: No QuestDB connection.")
                return

        try:
            self.sender.row(
                'market', # Table name
                symbols={'ticker': ticker, 'provider': source, 'interval': interval}, # Tags (indexed)
                columns={'close': price, 'open': price, 'high': price, 'low': price}, # Fields - map single price to OHLC
                at=TimestampNanos.from_datetime(timestamp) # Designated Timestamp
            )
            self.sender.flush()
        except IngressError as e:
            print(f"[{datetime.now()}] QuestDB Ingestion Error: {e}. Reconnecting...")
            self.connect()
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected Error inserting data: {e}. Reconnecting...")
            self.connect()

    def get_latest_timestamp(self, ticker: str):
        """
        Queries DB to find the last recorded timestamp for a symbol.
        Raises exception if query fails, to avoid false 'empty' detection.
        """
        try:
            query = f"SELECT max(ts) FROM market WHERE ticker = '{ticker}'"
            response = self.session.get(self.query_url, params={'query': query}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['dataset'] and data['dataset'][0][0]:
                    ts_str = data['dataset'][0][0]
                    return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                else:
                    return None
            else:
                err_text = response.text
                if "table does not exist" in err_text:
                    return None # New table, start fresh
                else:
                    raise Exception(f"QuestDB Query Failed: {err_text}")
        except Exception as e:
            print(f"[{datetime.now()}] Error querying latest timestamp: {e}")
            raise e
    
    def insert_bulk_data(self, ticker: str, data_list: list, source: str, interval: str = '1m'):
        """
        Inserts bulk data using HTTP REST API for reliability and error feedback.
        """
        if not data_list:
            return
            
        # Extract interval if present in first row, or default? 
        # Better to pass it as arg, but let's see. 
        # Actually, for bulk, let's allow passing it or hardcode '1m' for now if not passed.
        # Let's add kwargs to the method signature in a separate edit if needed, 
        # but for now I'll just infer or add it to the loop if the caller passes it?
        # The caller 'service.py' doesn't pass it yet.
        # Let's update the signature first.

        if not data_list:
            return

        write_url = f"http://{self.host}:{self.port - 9}/write" # Assuming HTTP port is Ingest Port - 9 (9000 vs 9009)
        # Or better, use the query port we already know
        write_url = self.query_url.replace('/exec', '/write') # http://localhost:9000/write

        rows_ilp = []
        for row in data_list:
            try:
                # 1. Tags
                # QuestDB requires specific escaping for tags, but for simple symbols/source it's fine.
                tags = f"ticker={ticker},provider={source},interval={interval}"

                # 2. Fields
                fields = []
                
                # Helper to format values
                def fmt(val):
                    if isinstance(val, int): return f"{val}i"
                    if isinstance(val, float): return str(round(val, 8))
                    return str(val)

                if 'open' in row and 'close' in row:
                     fields.append(f"open={round(row['open'], 8)}")
                     fields.append(f"high={round(row['high'], 8)}")
                     fields.append(f"low={round(row['low'], 8)}")
                     fields.append(f"close={round(row['close'], 8)}")
                else:
                    # Tiingo live style
                    p = row.get('close') or row.get('last')
                    if p: 
                        p = round(p, 8)
                        fields.append(f"close={p}")
                        # Optionally fill OHL if missing
                        if 'open' not in row: fields.append(f"open={p}")
                        if 'high' not in row: fields.append(f"high={p}")
                        if 'low'  not in row: fields.append(f"low={p}")

                if 'volume' in row:
                     fields.append(f"volume={round(row['volume'], 8)}")
                
                if not fields:
                    continue
                
                fields_str = ",".join(fields)

                # 3. Timestamp (Epoch Nanos)
                ts_val = row.get('date') if 'date' in row else row.get('timestamp')
                ts_nanos = 0
                
                if isinstance(ts_val, (int, float)):
                    # Binance sends millis (13 digits), QuestDB wants Nanos (19 digits)
                    # Use integer math to avoid float precision loss
                    ts_nanos = int(ts_val) * 1_000_000    
                else:
                    # String ISO format
                    dt = datetime.fromisoformat(str(ts_val).replace('Z', '+00:00'))
                    ts_nanos = int(dt.timestamp() * 1_000_000_000)

                # ILP Line: table,tags fields timestamp
                if ts_nanos == 0:
                    print(f"Skipping row with 0 timestamp (missing date): {row}")
                    continue
                    
                line = f"market,{tags} {fields_str} {ts_nanos}"
                rows_ilp.append(line)

            except Exception as e:
                print(f"Skipping malformed row: {row} | Error: {e}")

        payload = "\n".join(rows_ilp)
        
        try:
            r = self.session.post(write_url, data=payload)
            if r.status_code == 204:
                print(f"[{datetime.now()}] Successfully inserted {len(data_list)} rows for {ticker} (HTTP).")
            else:
                 print(f"[{datetime.now()}] INSERT ERROR {r.status_code}: {r.text}")
                 # Stop if we hit a hard error to avoid continuing blindly
                 raise Exception(f"QuestDB Insert Failed: {r.text}")
        except Exception as e:
             print(f"[{datetime.now()}] HTTP Connection Error: {e}")
             raise e
