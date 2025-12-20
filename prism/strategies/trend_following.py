from strategies.base_strategy import Strategy

class TrendFollowing(Strategy):
    """
    A simple Trend Following strategy.
    It buys if Price > Moving Average, Sells if Price < Moving Average.
    """
    def __init__(self, symbol: str, window: int = 5):
        super().__init__(symbol)
        self.window = window
        self.history = [] # Keep track of last N prices
        print(f"Strategy {self.__class__.__name__} initialized for {symbol}")

    def on_start(self, historical_data):
        """
        Warm up with history.
        """
        # historical_data is expected to be a list of dicts or similar
        print(f"Warming up with {len(historical_data)} records...")
        for row in historical_data:
            # Assuming row has 'price' (and we might ignore timestamp for simple logic)
            # Adapt based on actual data structure from QuestDB
            price = row.get('price') or row.get('close')
            if price:
                self.history.append(float(price))
                if len(self.history) > self.window:
                    self.history.pop(0)

    def on_tick(self, price, timestamp):
        """
        Main logic.
        """
        self.history.append(price)
        if len(self.history) > self.window:
            self.history.pop(0)
        
        if len(self.history) < self.window:
            return # Not enough data
        
        # Calculate Simple Moving Average
        sma = sum(self.history) / len(self.history)
        
        signal = "HOLD"
        if price > sma:
            signal = "BUY (Bullish)"
        elif price < sma:
            signal = "SELL (Bearish)"
            
        print(f"STRATEGY: Price {price} | SMA({self.window}): {sma:.2f} | Signal: {signal}")
