import datetime as dt
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

dag = DAG(
    dag_id="08_templated_paths",
    start_date=dt.datetime(2021, 8, 21),
    schedule_interval="@daily",
    end_date=dt.datetime(2021, 8, 28),
)

fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command=(
        "mkdir -p /data/events && "
        "curl -o /data/events/{{ds}}.json "
        "http://events_api:5000/events?"
        # "start_date={{execution_date.strftime('%Y-%m-%d')}}&"
        "start_date={{ds}}&"  # shorthand for the above
        # "end_date={{next_execution_date.strftime('%Y-%m-%d')}}"
        "end_date={{next_ds}}"  # shorthand for the above
    ),
    dag=dag,
)


def _calculate_stats(**context):
    """Calculate events statistics"""
    templates_dict = context["templates_dict"]

    input_path = templates_dict["input_path"]
    output_path = templates_dict["output_path"]

    events = pd.read_json(input_path)
    if events.size == 0:
        print("No elements")
        return
    # load the events and calculate the required statistics
    stats = events.groupby(["date", "user"]).size().reset_index()
    Path(output_path).parent.mkdir(exist_ok=True)
    stats.to_csv(output_path, index=False)


calculate_stats = PythonOperator(
    task_id="calculate_stats",
    python_callable=_calculate_stats,
    templates_dict={
        "input_path": "/data/events/{{ds}}.json",
        "output_path": "/data/stats/{{ds}}.csv",
    },
    # op_kwargs={"input_path": "/data/events.json", "output_path": "/data/stats.csv"},
    dag=dag,
)

fetch_events >> calculate_stats
