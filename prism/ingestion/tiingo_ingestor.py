import os
import requests
import json
from datetime import datetime

class TiingoProcessor:
    """
    Processor to interact with Tiingo API.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TIINGO_API_KEY")
        if not self.api_key:
            raise ValueError("TIINGO_API_KEY environment variable is not set.")
        
        self.base_url = "https://api.tiingo.com/iex"
        print(f"[{datetime.now()}] TiingoProcessor Initialized.")

    def get_latest_price(self, ticker: str):
        """
        Fetches the latest price for a ticker from Tiingo IEX endpoint.
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.api_key}'
        }
        
        try:
            url = f"{self.base_url}/{ticker}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # data is a list of objects, we take the first one
                    return data[0] 
            elif response.status_code == 429:
                print(f"[{datetime.now()}] API Limit Reached (429). Pausing for a bit...")
                return None
            else:
                print(f"Error fetching data: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception during Tiingo request: {e}")
            return None

    def get_historical_data(self, ticker: str, start_date: str, end_date: str = None):
        """
        Fetches EOD historical data.
        Dates format: YYYY-MM-DD
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.api_key}'
        }
        # Endpoint for daily data
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
        params = {
            'startDate': start_date,
            'resampleFreq': 'daily' 
        }
        if end_date:
            params['endDate'] = end_date

        try:
            print(f"[{datetime.now()}] Fetching historical data for {ticker} from {start_date}...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[{datetime.now()}] Retrieved {len(data)} historical records.")
                return data
            elif response.status_code == 429:
                 print(f"[{datetime.now()}] API Limit Reached (429).")
                 return []
            else:
                print(f"Error fetching history: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Exception during Tiingo history request: {e}")
            return []
