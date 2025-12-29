import os
from dotenv import load_dotenv

# Cargar variables del archivo .env si existe
load_dotenv()

class Config:
    """
    Central configuration for Prism.
    Reads from environment variables or uses defaults.
    """
    
    # 1. Trading Target
    # El ticker o activo principal que vamos a operar/analizar
    TARGET_TICKER = os.getenv("TARGET_TICKER", "BTCUSDT")
    
    # 2. Data Source
    # Fuente de datos: 'binance' o 'tiingo'
    DATA_SOURCE = os.getenv("DATA_SOURCE", "binance").lower()
    
    # 3. Backfill Configuration
    # Fecha de inicio para descargar datos históricos (Formato libre entendible, ej: "1 Jan, 2025" o "2025-01-01")
    BACKFILL_START_DATE = os.getenv("BACKFILL_START_DATE", "1 Jan, 2025")
    
    # 4. Data Details
    # Intervalo de velas para Binance (1m, 1h, 1d, etc.)
    # Recomendado 1m para máxima granularidad histórica
    KLINE_INTERVAL = os.getenv("KLINE_INTERVAL", "1m")
    
    # 5. API Keys (Ya existentes)
    TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

    # 5. Database Config
    # If running locally (not in docker compose network), use 'localhost'
    # 'questdb' is the hostname within the docker network usually.
    # We'll try to be smart or default to localhost if not set.
    QUESTDB_HOST = os.getenv("QUESTDB_HOST", "localhost")
    QUESTDB_PORT = int(os.getenv("QUESTDB_PORT", 9009))

    @classmethod
    def print_config(cls):
        print("------------- Prism Configuration -------------")
        print(f"Target Ticker:     {cls.TARGET_TICKER}")
        print(f"Data Source:       {cls.DATA_SOURCE}")
        print(f"Backfill Start:    {cls.BACKFILL_START_DATE}")
        print(f"QuestDB Host:      {cls.QUESTDB_HOST}:{cls.QUESTDB_PORT}")
        print("-----------------------------------------------")
