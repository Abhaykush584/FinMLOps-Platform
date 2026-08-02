# File: ml/feature_store.py

import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "symbolic-folio-491316-s8"
DATASET_ID = "raw_financial_data"
TABLE_ID = "fct_stock_ml_features"

def get_features() -> pd.DataFrame:
    """
    Connects to BigQuery and pulls the latest calculated ML features.
    Returns a Pandas DataFrame ordered chronologically.
    """
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
        SELECT * 
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` 
        ORDER BY price_date ASC
    """
    
    df = client.query(query).to_dataframe()
    return df