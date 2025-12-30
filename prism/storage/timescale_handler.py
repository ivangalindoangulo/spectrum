import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from datetime import datetime, timezone
import time

class TimescaleHandler:
    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        self.conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname
        }
        self.conn = None
        print(f"[{datetime.now()}] TimescaleHandler Initialized ({host}:{port})")
        
        self.connect()
        self.init_db()

    def connect(self):
        """Initializes the database connection."""
        try:
            if self.conn:
                self.conn.close()
            
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = True
            print(f"[{datetime.now()}] TimescaleDB Connection established.")
        except Exception as e:
            print(f"[{datetime.now()}] Failed to connect to TimescaleDB: {e}")
            self.conn = None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            try:
                self.conn.close()
                print(f"[{datetime.now()}] TimescaleDB Connection closed.")
            except Exception as e:
                print(f"[{datetime.now()}] Error closing TimescaleDB connection: {e}")
            finally:
                self.conn = None

    def init_db(self):
        """Creates the necessary tables and hypertable."""
        if not self.conn:
            return

        queries = [
            """
            CREATE TABLE IF NOT EXISTS market (
                ts TIMESTAMPTZ NOT NULL,
                ticker TEXT NOT NULL,
                provider TEXT NOT NULL,
                interval TEXT NOT NULL,
                open DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                close DOUBLE PRECISION,
                volume DOUBLE PRECISION
            );
            """,
            """
            SELECT create_hypertable('market', 'ts', if_not_exists => TRUE);
            """
        ]

        try:
            with self.conn.cursor() as cur:
                for q in queries:
                    cur.execute(q)
            print(f"[{datetime.now()}] Database initialized (Table 'market' ready).")
        except Exception as e:
            print(f"[{datetime.now()}] Error initializing database: {e}")

    def insert_market_data(self, ticker: str, price: float, timestamp: datetime, source: str, interval: str = '1m'):
        """
        Inserts a single market data point.
        """
        if not self.conn:
            self.connect()
            if not self.conn:
                return

        try:
            with self.conn.cursor() as cur:
                query = sql.SQL("""
                    INSERT INTO market (ts, ticker, provider, interval, close, open, high, low)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """)
                cur.execute(query, (timestamp, ticker, source, interval, price, price, price, price))
        except Exception as e:
            print(f"[{datetime.now()}] Error inserting data: {e}. Reconnecting...")
            self.connect()

    def get_latest_timestamp(self, ticker: str):
        """
        Queries DB to find the last recorded timestamp for a symbol.
        """
        if not self.conn:
            self.connect()
            if not self.conn:
                return None

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT max(ts) FROM market WHERE ticker = %s", (ticker,))
                result = cur.fetchone()
                if result and result[0]:
                    return result[0]
                else:
                    return None
        except Exception as e:
            print(f"[{datetime.now()}] Error querying latest timestamp: {e}")
            # If table doesn't exist, it might throw, but init_db should have handled it.
            # If we lost connection, reconnection logic is needed next time.
            return None
    
    def insert_bulk_data(self, ticker: str, data_list: list, source: str, interval: str = '1m'):
        """
        Inserts bulk data using execute_values for performance.
        """
        if not data_list:
            return
        
        if not self.conn:
            self.connect()
            if not self.conn:
                return

        # Prepare list of tuples
        rows = []
        for row in data_list:
            try:
                # Timestamp parsing
                ts_val = row.get('date') if 'date' in row else row.get('timestamp')
                if isinstance(ts_val, (int, float)):
                    # Assuming ms for Binance
                    ts = datetime.fromtimestamp(ts_val / 1000, tz=timezone.utc)
                else:
                    # ISO string
                    ts = datetime.fromisoformat(str(ts_val).replace('Z', '+00:00'))

                # Prices
                if 'open' in row:
                    open_p = row['open']
                    high_p = row['high']
                    low_p = row['low']
                    close_p = row['close']
                    vol = row.get('volume', 0.0)
                else:
                    p = float(row.get('close') or row.get('last') or 0.0)
                    open_p = high_p = low_p = close_p = p
                    vol = 0.0

                rows.append((ts, ticker, source, interval, open_p, high_p, low_p, close_p, vol))

            except Exception as e:
                print(f"Skipping row: {e}")
                continue

        try:
            with self.conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO market (ts, ticker, provider, interval, open, high, low, close, volume)
                    VALUES %s
                    """,
                    rows
                )
            print(f"[{datetime.now()}] Successfully inserted {len(rows)} rows for {ticker}.")
        except Exception as e:
            print(f"[{datetime.now()}] Bulk insert failed: {e}")
            self.connect()

    def get_history(self, ticker: str, limit: int = 100):
        """
        Selects recent history.
        """
        if not self.conn:
             self.connect()
             if not self.conn: return []

        try:
            with self.conn.cursor() as cur:
                # Return dictionary-like objects
                # We can use RealDictCursor globally or just map it here.
                # Let's map manually to keep it simple or use dictionary cursor if easy.
                # Standard cursor returns tuples.
                
                cur.execute("""
                    SELECT ts, ticker, provider, interval, open, high, low, close, volume 
                    FROM market 
                    WHERE ticker = %s 
                    ORDER BY ts DESC 
                    LIMIT %s
                """, (ticker, limit))
                
                cols = [desc[0] for desc in cur.description]
                results = []
                for row in cur.fetchall():
                    results.append(dict(zip(cols, row)))
                
                # Reverse to have chronological order if needed (runner expects DESC for limit, but often processes chronological?)
                # Runner.get_history reversed it. Let's see runner logic.
                # Runner: "dataset is ordered DESC... so we should reverse it for warm-up"
                # So we return DESC here as well (latest first).
                
                return results
                
        except Exception as e:
            print(f"[{datetime.now()}] Error querying history: {e}")
            return []

    def get_latest(self, ticker: str):
        """
        Polls for the absolute latest record.
        """
        if not self.conn:
             self.connect()
             if not self.conn: return None

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT ts, ticker, provider, interval, open, high, low, close, volume 
                    FROM market 
                    WHERE ticker = %s 
                    ORDER BY ts DESC 
                    LIMIT 1
                """, (ticker,))
                
                row = cur.fetchone()
                if row:
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, row))
                return None
        except Exception as e:
            return None
