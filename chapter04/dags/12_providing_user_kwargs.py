from urllib import request

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils import dates

dag = DAG(
    dag_id="12_providing_user_kwargs",
    start_date=dates.days_ago(1),
    schedule_interval="@daily",
)


def _get_data(output_path, **context):
    year, month, day, hour, *_ = context["execution_date"].timetuple()
    url = (
        "https://dumps.wikimedia.org/other/pageviews/"
        f"{year}/{year}-{month:0>2}/pageviews-{year}{month:0>2}{day:0>2}-{hour:0>2}0000.gz"
    )
    request.urlretrieve(url, output_path)


get_data = PythonOperator(
    task_id="get_data",
    python_callable=_get_data,
    op_kwargs={"output_path": "/tmp/wikipageviews.gz"},
    dag=dag,
)
