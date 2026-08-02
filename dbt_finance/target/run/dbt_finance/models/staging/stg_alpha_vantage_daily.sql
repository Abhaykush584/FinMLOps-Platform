

  create or replace view `symbolic-folio-491316-s8`.`raw_financial_data`.`stg_alpha_vantage_daily`
  OPTIONS()
  as -- File: dbt_finance/models/staging/stg_alpha_vantage_daily.sql

WITH source_data AS (
    SELECT * 
    FROM `symbolic-folio-491316-s8.raw_financial_data.raw_daily_stock_prices`
)

SELECT
    PARSE_DATE('%Y-%m-%d', date) AS price_date,
    symbol,
    CAST(open AS FLOAT64) AS open_price,
    CAST(high AS FLOAT64) AS high_price,
    CAST(low AS FLOAT64) AS low_price,
    CAST(close AS FLOAT64) AS close_price,
    CAST(volume AS INT64) AS volume
FROM source_data
-- Deduplicates records if you fetch API data multiple times
QUALIFY ROW_NUMBER() OVER(PARTITION BY symbol, date ORDER BY date) = 1;

