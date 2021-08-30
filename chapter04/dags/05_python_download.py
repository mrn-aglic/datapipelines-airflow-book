from urllib import request

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils import dates

dag = DAG(
    dag_id="05_python_download",
    start_date=dates.days_ago(1),
    schedule_interval="@daily",
)


def _print_context(**context):
    start = context["execution_date"]
    end = context["next_execution_date"]
    print(f"Start: {start}, end: {end}")


print_context = PythonOperator(
    task_id="print_context",
    python_callable=_print_context,
    dag=dag,
)

# def _get_data(execution_date, **context):
def _get_data(execution_date):
    year, month, day, hour, *_ = execution_date.timetuple()
    url = (
        "https://dumps.wikimedia.org/other/pageviews/"
        f"{year}/{year}-{month:0>2}/"
        f"pageviews-{year}{month:0>2}{day:0>2}-{hour:0>2}0000.gz"
    )
    output_path = "/tmp/wikipageviews.gz"
    request.urlretrieve(url, output_path)


get_data = PythonOperator(
    task_id="get_data",
    python_callable=_get_data,
    dag=dag,
)
