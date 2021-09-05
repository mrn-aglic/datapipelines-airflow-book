from pathlib import Path

from airflow import DAG
from airflow.sensors.python import PythonSensor
from airflow.utils import dates

dag = DAG(
    dag_id="02_python_sensor",
    start_date=dates.days_ago(3),
    schedule_interval="0 16 * * *",
    description="A batch workflow for ingesting supermarket promotions data.",
    default_args={"depends_on_past": True},
)


def _wait_for_supermarket(supermarket_id):
    supermarket_path = Path(f"/data/{supermarket_id}")
    data_files = supermarket_path.glob("data-*.csv")
    success_file = supermarket_path / "_SUCCESS"
    return data_files and success_file.exists()


wait_for_supermarket_1 = PythonSensor(
    task_id="wait_for_supermarket_1",
    python_callable=_wait_for_supermarket,
    op_kwargs={"supermarket_id": "supermarket1"},
    dag=dag,
)
