from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.latest_only import LatestOnlyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.utils import dates

ERP_CHANGE_DATE = dates.days_ago(1)


def _pick_erp_system(**context):
    if context["execution_date"] < ERP_CHANGE_DATE:
        return "fetch_sales_old"
    else:
        return "fetch_sales_new"


with DAG(
    dag_id="19_condition_dag_op",
    start_date=dates.days_ago(3),
    schedule_interval="@daily",
) as dag:
    start = DummyOperator(task_id="start")

    pick_erp_system = BranchPythonOperator(
        task_id="pick_erp_system", python_callable=_pick_erp_system
    )

    fetch_sales_old = DummyOperator(task_id="fetch_sales_old")
    clean_sales_old = DummyOperator(task_id="clean_sales_old")

    fetch_sales_new = DummyOperator(task_id="fetch_sales_new")
    clean_sales_new = DummyOperator(task_id="clean_sales_new")

    join_erp = DummyOperator(task_id="join_erp_branch", trigger_rule="none_failed")

    fetch_weather = DummyOperator(task_id="fetch_weather")
    clean_weather = DummyOperator(task_id="clean_weather")

    join_datasets = DummyOperator(task_id="join_datasets")
    train_model = DummyOperator(task_id="train_model")

    latest_only = LatestOnlyOperator(task_id="latest_only")
    deploy_model = DummyOperator(task_id="deploy_model")

    start >> [pick_erp_system, fetch_weather]  # fan-out dependency
    pick_erp_system >> [fetch_sales_old, fetch_sales_new]
    fetch_sales_old >> clean_sales_old  # linear dependency
    fetch_sales_new >> clean_sales_new
    fetch_weather >> clean_weather  # linear dependency
    (
        [
            clean_sales_old,
            clean_sales_new,
        ]
        >> join_erp
    )
    [join_erp, clean_weather] >> join_datasets
    join_datasets >> train_model >> latest_only >> deploy_model  # linear dependency