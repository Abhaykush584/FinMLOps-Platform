
  
    

    create or replace table `symbolic-folio-491316-s8`.`raw_financial_data`.`fct_stock_ml_features`
      
    
    

    OPTIONS()
    as (
      -- File: dbt_finance/models/marts/fct_stock_ml_features.sql

WITH clean_prices AS (
    SELECT * 
    FROM `symbolic-folio-491316-s8`.`raw_financial_data`.`stg_alpha_vantage_daily`
),

technical_indicators AS (
    SELECT
        price_date,
        symbol,
        close_price,
        volume,
        
        -- Daily percentage return
        (close_price - LAG(close_price, 1) OVER (PARTITION BY symbol ORDER BY price_date)) 
            / NULLIF(LAG(close_price, 1) OVER (PARTITION BY symbol ORDER BY price_date), 0) AS daily_return,

        -- 5-day Moving Average
        AVG(close_price) OVER (
            PARTITION BY symbol ORDER BY price_date 
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS ma_5,

        -- 20-day Moving Average
        AVG(close_price) OVER (
            PARTITION BY symbol ORDER BY price_date 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS ma_20,

        -- Next day's close price (for target calculation)
        LEAD(close_price, 1) OVER (PARTITION BY symbol ORDER BY price_date) AS next_day_close

    FROM clean_prices
)

SELECT
    price_date,
    symbol,
    close_price,
    volume,
    daily_return,
    ma_5,
    ma_20,
    -- Target for ML Classification: 1 if tomorrow's price > today's price, else 0
    CASE 
        WHEN next_day_close > close_price THEN 1 
        ELSE 0 
    END AS target_direction
FROM technical_indicators
WHERE ma_20 IS NOT NULL -- Drops initial rows where 20-day MA can't be calculated
  AND next_day_close IS NOT NULL -- Drops the most recent day since tomorrow's price is unknown
ORDER BY price_date ASC
    );
  