import os

from airflow.models import Connection
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflowbook.hooks import MovielensHook
from airflowbook.operators.movielens_operators import MovielensToPostgresOperator
from pytest_docker_tools import build, container

POSTGRES_PORT = 5432

# doesn'T work with newer postgres repo - don't know why
# postgres_image = fetch(repository="postgres:11.1-alpine")
postgres_image = build(
    path=os.path.join(os.path.dirname(__file__), "docker")
)  # it is simpler to build given our setup

postgres = container(
    image="{postgres_image.id}",
    name="my_pytest_container",
    scope="function",
    ports={f"{POSTGRES_PORT}/tcp": None},
    network="chapter08_default",
    environment={
        "POSTGRES_USER": "testuser",
        "POSTGRES_PASSWORD": "testpass",
    },
    # volumes={
    #     os.path.join(os.path.dirname(__file__), "postgres-init.sql"): {
    #         "bind": "/docker-entrypoint-initdb.d/postgres-init.sql"
    #     }
    # }, # Might be complicated to setup with running tests inside of a docker env
)


def test_movielens_to_postgres_operator(mocker, test_dag, postgres):
    mocker.patch.object(
        MovielensHook,
        "get_connection",
        return_value=Connection(
            conn_id="test",
            login="airflow",
            password="airflow",
            host="movielens-api",
        ),
    )

    mocker.patch.object(
        PostgresHook,
        "get_connection",
        return_value=Connection(
            conn_id="postgres",
            conn_type="postgres",
            host="my_pytest_container",
            login="testuser",
            password="testpass",
            port=POSTGRES_PORT,  # we are connecting to a docker container from a docker container so use internal port
        ),
    )

    task = MovielensToPostgresOperator(
        task_id="test",
        movielens_conn_id="movielens_id",
        start_date="{{ ds }}",
        end_date="{{ data_interval_end | ds }}",
        postgres_conn_id="postgres_id",
        insert_query="INSERT INTO movielens (movieId, rating, ratingTimestamp, userId, scrapeTime)"
        "VALUES ({0}, '{{ macros.datetime.now() }}')",
        dag=test_dag,
    )

    pg_hook = PostgresHook()
    row_count = pg_hook.get_first("SELECT COUNT(*) FROM movielens")[0]
    assert row_count == 0

    task.run(
        start_date=test_dag.default_args["start_date"],
        end_date=test_dag.default_args["start_date"],
        ignore_ti_state=True,
    )

    row_count = pg_hook.get_first("SELECT COUNT(*) FROM movielens")[0]
    assert row_count > 0


postgres_container = container(image="{postgres_image.id}", ports={"5432/tcp": None})


def test_call_fixture(postgres_container):
    print(
        f"Running Postgres container named {postgres_container.name}"
        f" on port {postgres_container.ports[f'{POSTGRES_PORT}/tcp']}."
    )
