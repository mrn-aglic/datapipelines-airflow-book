from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.utils import dates

dag = DAG(
    dag_id="figure_01",
    start_date=dates.days_ago(3),
    schedule_interval="0 16 * * *",
    description="A batch workflow for ingesting supermarket promotions data, demonstrating the FileSensor.",
    default_args={"depends_on_past": True},
)

create_metrics = DummyOperator(task_id="create_metrics", dag=dag)

for market_id in range(1, 5):
    copy = DummyOperator(task_id=f"copy_to_raw_supermarket_{market_id}", dag=dag)
    process = DummyOperator(task_id=f"process_supermarket_{market_id}", dag=dag)
    copy >> process >> create_metrics
