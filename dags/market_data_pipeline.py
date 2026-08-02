# File: dags/market_data_pipeline.py

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default settings for the pipeline
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 7, 31), # Starts running from today
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG (runs daily)
with DAG(
    'market_data_ml_pipeline',
    default_args=default_args,
    description='End-to-End Financial ELT and ML Training Pipeline',
    schedule_interval='@daily',
    catchup=False,
) as dag:

    # Step 1: Ingest raw data from Alpha Vantage to BigQuery
    ingest_task = BashOperator(
        task_id='ingest_daily_market_data',
        bash_command='python /opt/airflow/ingestion/alpha_vantage_client.py'
    )

    # Step 2: Transform raw strings into ML features using dbt
    dbt_transform_task = BashOperator(
        task_id='dbt_feature_engineering',
        bash_command='cd /opt/airflow/dbt_finance && python -m dbt.cli.main run --profiles-dir .'
    )

    # Step 3: Retrain the XGBoost model on the newly updated dataset
    train_model_task = BashOperator(
        task_id='retrain_ml_model',
        bash_command='python /opt/airflow/ml/train.py'
    )

    # Define the execution order
    ingest_task >> dbt_transform_task >> train_model_task