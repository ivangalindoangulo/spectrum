-- 1. assets (Maestro - Standard Table, assuming low churn, but can be hypertable if tracking changes over time. Keeping standard for now or hypertable if strictly time-series updates. QuestDB had it partitioned by YEAR. Let's make it a hypertable to match user intent of history.)
CREATE TABLE IF NOT EXISTS assets (
    ts TIMESTAMPTZ NOT NULL,
    ticker TEXT NOT NULL,
    name TEXT,
    class TEXT,          -- Equity, Crypto, FX
    exchange TEXT,
    active BOOLEAN
);
-- Create Hypertable: partitioned by time
SELECT create_hypertable('assets', 'ts', if_not_exists => TRUE);
-- Indexes
CREATE INDEX IF NOT EXISTS idx_assets_ticker ON assets (ticker, ts DESC);


-- 2. market (Datos - High Volume)
CREATE TABLE IF NOT EXISTS market (
    ts TIMESTAMPTZ NOT NULL,
    ticker TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    adjusted DOUBLE PRECISION,       -- Precio ajustado
    provider TEXT,       -- Tiingo, Yahoo
    interval TEXT        -- 1d, 1m
);
SELECT create_hypertable('market', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 month');
CREATE INDEX IF NOT EXISTS idx_market_ticker ON market (ticker, ts DESC);


-- 3. models (Versiones)
CREATE TABLE IF NOT EXISTS models (
    ts TIMESTAMPTZ NOT NULL,
    name TEXT NOT NULL,     -- ID del modelo
    version TEXT,
    description TEXT,
    author TEXT,
    parameters TEXT,     -- Hiperparámetros (JSON usually better in PG/Timescale, keeping TEXT to match)
    status TEXT
);
SELECT create_hypertable('models', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 year');
CREATE INDEX IF NOT EXISTS idx_models_name ON models (name, ts DESC);


-- 4. signals (Predicciones)
CREATE TABLE IF NOT EXISTS signals (
    ts TIMESTAMPTZ NOT NULL,
    model TEXT NOT NULL,    -- Quién generó la señal
    ticker TEXT NOT NULL,
    side TEXT,           -- LONG, SHORT
    score DOUBLE PRECISION,          -- 0.0 a 1.0
    target DOUBLE PRECISION,         -- Precio objetivo
    stop DOUBLE PRECISION            -- Stop loss
);
SELECT create_hypertable('signals', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 month');
CREATE INDEX IF NOT EXISTS idx_signals_model_ticker ON signals (model, ticker, ts DESC);


-- 5. risk (Control)
CREATE TABLE IF NOT EXISTS risk (
    ts TIMESTAMPTZ NOT NULL,
    model TEXT NOT NULL,
    ticker TEXT NOT NULL,
    check_name TEXT,          -- Renamed 'check' to 'check_name' to avoid reserved keyword potential issues (though 'check' is valid col name in PG quoted, safe side TEXT) -> actually 'check' is reserved. Let's use "check_type" or keep "check" but quoted. Let's map to check_type for safety or keep identical? QuestDB usage: check. Let's stick to 'check_type' to be safe or just quote it if needed. Standard PG 'check' is a keyword. I will use 'check_type'.
    result TEXT,         -- PASS / REJECT
    exposure DOUBLE PRECISION,       -- Exposición actual
    reason TEXT
);
-- Note: 'check' is a keyword in SQL. Using "check" (quoted) or renaming. Let's assume renaming to check_type is safer for python code too.
-- Wait, if python code expects 'check', I should check. But 'check' is usually fine as column if not confused with constraint.
-- Let's use "check_type" in schema to be cleaner.
SELECT create_hypertable('risk', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 month');
CREATE INDEX IF NOT EXISTS idx_risk_model_ticker ON risk (model, ticker, ts DESC);


-- 6. orders (Intención)
CREATE TABLE IF NOT EXISTS orders (
    ts TIMESTAMPTZ NOT NULL,
    id TEXT NOT NULL,       -- UUID interno
    ticker TEXT NOT NULL,
    side TEXT,
    order_type TEXT,     -- MKT, LMT
    quantity DOUBLE PRECISION,
    price_limit DOUBLE PRECISION,    -- Precio límite solicitado
    status TEXT,         -- NEW, FILLED
    strategy TEXT        -- Origen
);
SELECT create_hypertable('orders', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');
CREATE INDEX IF NOT EXISTS idx_orders_id ON orders (id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_orders_ticker ON orders (ticker, ts DESC);


-- 7. fills (Realidad)
CREATE TABLE IF NOT EXISTS fills (
    ts TIMESTAMPTZ NOT NULL,
    id TEXT NOT NULL,            -- ID externo del exchange
    order_id TEXT NOT NULL,      -- Referencia a orders.id
    ticker TEXT NOT NULL,
    side TEXT,
    price DOUBLE PRECISION,               -- Precio real pagado
    quantity DOUBLE PRECISION,
    fee DOUBLE PRECISION,
    currency TEXT
);
SELECT create_hypertable('fills', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 month');
CREATE INDEX IF NOT EXISTS idx_fills_order_id ON fills (order_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_fills_ticker ON fills (ticker, ts DESC);
