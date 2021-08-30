import pendulum
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.utils import dates

ERP_CHANGE_DATE = dates.days_ago(1)


def _pick_erp_system(**context):
    if context["execution_date"] < ERP_CHANGE_DATE:
        return "fetch_sales_old"
    else:
        return "fetch_sales_new"


def _is_latest_run(execution_date, dag: DAG, **_):
    now = pendulum.now("UTC")
    left_window = dag.following_schedule(execution_date)
    right_window = dag.following_schedule(left_window)
    return left_window < now <= right_window


def _deploy(execution_date, dag: DAG, **_):
    if _is_latest_run(execution_date, dag):
        print("Deploy model")


with DAG(
    dag_id="16_condition_task",
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

    deploy_model = PythonOperator(task_id="deploy_model", python_callable=_deploy)

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
    join_datasets >> train_model >> deploy_model  # linear dependency
