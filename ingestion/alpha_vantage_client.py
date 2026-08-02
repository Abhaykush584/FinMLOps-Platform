import requests
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# --- CONFIGURATION ---
API_KEY = "51GPTQ89P7H3SN9N"
PROJECT_ID = "symbolic-folio-491316-s8"
DATASET_ID = "raw_financial_data"
TABLE_ID = "raw_daily_stock_prices"

def run_ingestion():
    print("Fetching data from Alpha Vantage...")
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "Time Series (Daily)" not in data:
        print("\n❌ API Error or Rate Limit hit! Here is what Alpha Vantage returned:\n")
        print(data)
        return

    # 1. Convert JSON response to Pandas DataFrame
    daily_records = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(daily_records, orient="index").reset_index()
    df.columns = ["date", "open", "high", "low", "close", "volume"]
    df["symbol"] = "AAPL"

    # 2. Connect to BigQuery
    print("Connecting to BigQuery...")
    client = bigquery.Client(project=PROJECT_ID)

    # 3. Check and create Dataset automatically if it doesn't exist
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset '{DATASET_ID}' verified.")
    except NotFound:
        print(f"Dataset '{DATASET_ID}' not found. Creating it automatically...")
        dataset_ref.location = "asia-south2"  # Matches your Delhi location selection
        client.create_dataset(dataset_ref, timeout=30)
        print(f"Dataset '{DATASET_ID}' created successfully!")

    # 4. Upload to BigQuery
    print("Uploading data to BigQuery...")
    table_address = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    job = client.load_table_from_dataframe(df, table_address)
    job.result()  # Wait for upload to complete

    print("✅ Success! Your raw financial data is in BigQuery.")

if __name__ == "__main__":
    run_ingestion()

    