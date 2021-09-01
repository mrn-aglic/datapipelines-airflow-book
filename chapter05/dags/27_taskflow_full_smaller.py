import uuid

from airflow import DAG
from airflow.decorators import task
from airflow.operators.dummy import DummyOperator
from airflow.utils import dates

with DAG(
    dag_id="27_taskflow_full_smaller",
    start_date=dates.days_ago(3),
    schedule_interval="@daily",
) as dag:
    start = DummyOperator(task_id="start")

    fetch_sales = DummyOperator(task_id="fetch_sales_new")
    clean_sales = DummyOperator(task_id="clean_sales_new")

    fetch_weather = DummyOperator(task_id="fetch_weather")
    clean_weather = DummyOperator(task_id="clean_weather")

    join_datasets = DummyOperator(task_id="join_datasets")

    @task
    def train_model():
        model_id = str(uuid.uuid4())
        return model_id

    @task
    def deploy_model(model_id: str):
        print(f"Deploying model {model_id}")

    model_id = train_model()
    deploy_model(model_id)

    start >> [fetch_sales, fetch_weather]  # fan-out dependency
    fetch_sales >> clean_sales  # linear dependency
    fetch_weather >> clean_weather  # linear dependency
    [
        clean_sales,
        clean_weather,
    ] >> join_datasets
    join_datasets >> model_id  # linear dependency
