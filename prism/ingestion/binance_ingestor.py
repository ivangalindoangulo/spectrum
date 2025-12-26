import os
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime
import pandas as pd

class BinanceProcessor:
    """
    Processor to interact with Binance API using python-binance library.
    """
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_SECRET_KEY")
        
        # Initialize the Client
        # If no keys are provided, it will work in public mode (some endpoints only)
        # but for full functionality (trading, user data), keys are required.
        self.client = Client(self.api_key, self.api_secret)
        
        print(f"[{datetime.now()}] BinanceProcessor Initialized.")

    def get_latest_price(self, symbol: str):
        """
        Fetches the latest price for a symbol (e.g., 'BTCUSDT').
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return ticker
        except BinanceAPIException as e:
            print(f"Binance API Exception: {e}")
            return None
        except Exception as e:
            print(f"Exception during Binance request: {e}")
            return None

    def get_historical_data(self, symbol: str, interval: str, start_str: str, end_str: str = None):
        """
        Fetches historical klines (candlestick) data.
        
        :param symbol: Trading pair, e.g., 'BTCUSDT'
        :param interval: Kline interval, e.g., Client.KLINE_INTERVAL_1DAY
        :param start_str: Start date string in UTC format or timestamp
        :param end_str: Optional end date string
        """
        try:
            print(f"[{datetime.now()}] Fetching historical data for {symbol} from {start_str}...")
            klines = self.client.get_historical_klines(symbol, interval, start_str, end_str)
            
            # Format: [Open time, Open, High, Low, Close, Volume, Close time, ...]
            # convert to dataframe or list of dicts as needed
            processed_data = []
            for k in klines:
                processed_data.append({
                    "timestamp": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": k[6]
                })
                
            print(f"[{datetime.now()}] Retrieved {len(processed_data)} historical records.")
            return processed_data

        except BinanceAPIException as e:
            print(f"Binance API Exception: {e}")
            return []
        except Exception as e:
            print(f"Exception during Binance history request: {e}")
            return []

    def get_account_info(self):
        """
        Get account information (requires API keys).
        """
        if not self.api_key or not self.api_secret:
            print("API Keys are required for account info.")
            return None
            
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            print(f"Binance API Exception: {e}")
            return None
