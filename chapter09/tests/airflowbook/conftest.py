from datetime import datetime

import pytest
from airflow import DAG


@pytest.fixture
def test_dag():
    return DAG(
        dag_id="test_dag",
        default_args={
            "owner": "airflow",
            "start_date": datetime(2019, 1, 1),
        },
        schedule_interval="@daily",
    )
