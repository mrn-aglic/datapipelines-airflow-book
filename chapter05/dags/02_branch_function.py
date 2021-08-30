from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.utils import dates

ERP_CHANGE_DATE = dates.days_ago(1)


def _fetch_sales_old(**context):
    print("Fetching sales data (OLD)...")


def _fetch_sales_new(**context):
    print("Fetching sales data (NEW)...")


def _fetch_sales(**context):
    if context["execution_date"] < ERP_CHANGE_DATE:
        _fetch_sales_old(**context)
    else:
        _fetch_sales_new(**context)


def _clean_sales_old(**context):
    print("Cleaning sales data (OLD)...")


def _clean_sales_new(**context):
    print("Cleaning sales data (NEW)...")


def _clean_sales(**context):
    if context["execution_date"] < ERP_CHANGE_DATE:
        _clean_sales_old(**context)
    else:
        _clean_sales_new(**context)


with DAG(
    dag_id="02_branch_function",
    start_date=dates.days_ago(3),
    schedule_interval="@daily",
) as dag:
    start = DummyOperator(task_id="start")

    fetch_sales = PythonOperator(task_id="fetch_sales", python_callable=_fetch_sales)
    clean_sales = PythonOperator(task_id="clean_sales", python_callable=_clean_sales)

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
