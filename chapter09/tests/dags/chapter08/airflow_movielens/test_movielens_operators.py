from airflow.models import Connection
from airflow.operators.bash import BashOperator
from airflowbook.hooks import MovielensHook
from airflowbook.operators.movielens_operators import MovielensPopularityOperator
from pytest_mock import MockFixture


def test_movielenspopularityoperator(mocker: MockFixture):
    n = 5

    mock_get = mocker.patch.object(
        MovielensHook,
        "get_connection",
        # I need to define host because my implementation of MovielensHook throws a ValueError if no host is specified.
        return_value=Connection(
            conn_id="test", host="movielens-api", login="airflow", password="airflow"
        ),
    )

    task = MovielensPopularityOperator(
        task_id="test_id",
        conn_id="testconn",
        start_date="2019-01-01",
        end_date="2019-01-03",
        top_n=n,
    )

    result = task.execute(context=None)
    assert len(result) == n
    assert (
        mock_get.call_count == 1
    )  # validate that get_connection is called exaclty once
    mock_get.assert_called_with(
        "testconn"
    )  # validate that get_connection holds the same conn_id
    # as provided to the MovielensPopularityOperator


def test_example():
    task = BashOperator(task_id="test", bash_command="echo 'hello!'", do_xcom_push=True)

    result = task.execute(context={})
    assert result == "hello!"
