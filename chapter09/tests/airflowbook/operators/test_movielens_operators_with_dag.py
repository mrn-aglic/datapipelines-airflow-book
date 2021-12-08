from pathlib import Path

from airflow.models import Connection
from airflowbook.hooks import MovielensHook
from airflowbook.operators.movielens_operators import MovielensDownloadOperator
from pytest_mock import MockFixture


def test_movielens_operator(tmp_path: Path, mocker: MockFixture, test_dag):
    mocker.patch.object(
        MovielensHook,
        "get_connection",
        return_value=Connection(
            conn_id="test", host="movielens-api", login="airflow", password="airflow"
        ),
    )

    task = MovielensDownloadOperator(
        task_id="test",
        conn_id="testconn",
        start_date="{{ prev_ds }}",
        end_date="{{ ds }}",
        output_path=str(tmp_path / "{{ ds }}.json"),
        dag=test_dag,
    )

    task.run(
        start_date=test_dag.default_args["start_date"],
        end_date=test_dag.default_args["start_date"],
    )
