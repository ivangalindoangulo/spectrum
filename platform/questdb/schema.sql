-- 1. assets (Maestro)
CREATE TABLE IF NOT EXISTS assets (
    ts TIMESTAMP,
    ticker SYMBOL INDEX,
    name STRING,
    class SYMBOL,          -- Equity, Crypto, FX
    exchange SYMBOL,
    active BOOLEAN
) TIMESTAMP(ts) PARTITION BY YEAR WAL;

-- 2. market (Datos)
CREATE TABLE IF NOT EXISTS market (
    ts TIMESTAMP,
    ticker SYMBOL INDEX,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    adjusted DOUBLE,       -- Precio ajustado
    provider SYMBOL,       -- Tiingo, Yahoo
    interval SYMBOL        -- 1d, 1m
) TIMESTAMP(ts) PARTITION BY MONTH WAL;

-- 3. models (Versiones)
CREATE TABLE IF NOT EXISTS models (
    ts TIMESTAMP,
    name SYMBOL INDEX,     -- ID del modelo
    version SYMBOL,
    description STRING,
    author SYMBOL,
    parameters STRING,     -- Hiperparámetros
    status SYMBOL
) TIMESTAMP(ts) PARTITION BY YEAR WAL;

-- 4. signals (Predicciones)
CREATE TABLE IF NOT EXISTS signals (
    ts TIMESTAMP,
    model SYMBOL INDEX,    -- Quién generó la señal
    ticker SYMBOL INDEX,
    side SYMBOL,           -- LONG, SHORT
    score DOUBLE,          -- 0.0 a 1.0
    target DOUBLE,         -- Precio objetivo
    stop DOUBLE            -- Stop loss
) TIMESTAMP(ts) PARTITION BY MONTH WAL;

-- 5. risk (Control)
CREATE TABLE IF NOT EXISTS risk (
    ts TIMESTAMP,
    model SYMBOL INDEX,
    ticker SYMBOL INDEX,
    check SYMBOL,          -- Tipo de chequeo (VaR)
    result SYMBOL,         -- PASS / REJECT
    exposure DOUBLE,       -- Exposición actual
    reason STRING
) TIMESTAMP(ts) PARTITION BY MONTH WAL;

-- 6. orders (Intención)
CREATE TABLE IF NOT EXISTS orders (
    ts TIMESTAMP,
    id SYMBOL INDEX,       -- UUID interno
    ticker SYMBOL INDEX,
    side SYMBOL,
    type SYMBOL,           -- MKT, LMT
    quantity DOUBLE,
    limit DOUBLE,          -- Precio límite solicitado
    status SYMBOL,         -- NEW, FILLED
    strategy SYMBOL        -- Origen
) TIMESTAMP(ts) PARTITION BY DAY WAL;

-- 7. fills (Realidad)
CREATE TABLE IF NOT EXISTS fills (
    ts TIMESTAMP,
    id SYMBOL INDEX,            -- ID externo del exchange
    order SYMBOL INDEX,         -- Referencia a orders.id
    ticker SYMBOL INDEX,
    side SYMBOL,
    price DOUBLE,               -- Precio real pagado
    quantity DOUBLE,
    fee DOUBLE,
    currency SYMBOL
) TIMESTAMP(ts) PARTITION BY MONTH WAL;
