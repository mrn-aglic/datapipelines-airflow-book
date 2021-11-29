import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from custom.movielens_hook import MovielensHook
from custom.ranking import rank_movies_by_rating


def _fetch_ratings(conn_id, templates_dict: dict, batch_size=1000, **_):
    logger = logging.getLogger(__name__)

    start_date = templates_dict["start_date"]
    end_date = templates_dict["end_date"]
    output_path = templates_dict["output_path"]

    logger.info("Fetching ratings for %s to %s", start_date, end_date)

    hook = MovielensHook(conn_id=conn_id)
    ratings = list(
        hook.get_ratings(
            start_date=start_date, end_date=end_date, batch_size=batch_size
        )
    )

    logger.info("Fetched %s ratings.", len(ratings))

    logger.info("Writing ratings to %s", output_path)

    path = output_path[: output_path.rfind("/")]
    Path(path).mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as file:
        json.dump(ratings, file)


def _rank_movies(templates_dict: dict, min_ratings=2, **_):
    logger = logging.getLogger(__name__)

    input_path = templates_dict["input_path"]
    output_path = templates_dict["output_path"]

    ratings = pd.read_json(input_path)
    ranking = rank_movies_by_rating(ratings, min_ratings)

    path = output_path[: output_path.rfind("/")]

    logger.info("Making sure path exists: %s", path)
    Path(path).mkdir(parents=True, exist_ok=True)

    logger.info("Storing rankings to: %s", output_path)
    ranking.to_csv(output_path, index=True)


with DAG(
    dag_id="02_fetch_ratings_hook", start_date=datetime(2019, 1, 1), max_active_runs=1
) as dag:
    fetch_ratings = PythonOperator(
        task_id="fetch_ratings",
        python_callable=_fetch_ratings,
        op_kwargs={"conn_id": "movielens"},
        templates_dict={
            "start_date": "{{ds}}",
            "end_date": "{{next_ds}}",
            "output_path": "/data/custom_hook/ratings/{{ds}}.json",
        },
    )

    rank_movies = PythonOperator(
        task_id="rank_movies",
        python_callable=_rank_movies,
        templates_dict={
            "input_path": "/data/custom_hook/ratings/{{ds}}.json",
            "output_path": "/data/custom_hook/rankings/{{ds}}.json",
        },
    )

    fetch_ratings >> rank_movies
