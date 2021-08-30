from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.utils import dates

with DAG(
    dag_id="01_start",
    start_date=dates.days_ago(1),
    schedule_interval="@daily",
) as dag:
    start = DummyOperator(task_id="start")

    fetch_sales = DummyOperator(task_id="fetch_sales")
    clean_sales = DummyOperator(task_id="clean_sales")

    fetch_weather = DummyOperator(task_id="fetch_weather")
    clean_weather = DummyOperator(task_id="clean_weather")

    join_datasets = DummyOperator(task_id="join_datasets")
    train_model = DummyOperator(task_id="train_model")
    deploy_model = DummyOperator(task_id="deploy_model")

    start >> [fetch_sales, fetch_weather]  # fan-out dependency
    fetch_sales >> clean_sales  # linear dependency
    fetch_weather >> clean_weather  # linear dependency
    [clean_sales, clean_weather] >> join_datasets  # fan-in dependency
    join_datasets >> train_model >> deploy_model  # linear dependency
