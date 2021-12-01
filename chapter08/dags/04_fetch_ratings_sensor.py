import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from custom.movielens_operator import MovielensFetchRatingsOperators
from custom.movielens_sensor import MovielensRatingsSensor
from custom.ranking import rank_movies_by_rating


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
    dag_id="04_fetch_ratings_sensor", start_date=datetime(2019, 1, 1), max_active_runs=3
) as dag:
    wait_for_ratings = MovielensRatingsSensor(
        task_id="wait_for_ratings",
        conn_id="movielens",
        start_date="{{ds}}",
        end_date="{{next_ds}}",
        retries=15,
    )

    fetch_ratings = MovielensFetchRatingsOperators(
        task_id="fetch_ratings",
        conn_id="movielens",
        start_date="{{ds}}",
        end_date="{{next_ds}}",
        output_path="/data/custom_sensor/ratings/{{ds}}.json",
    )

    rank_movies = PythonOperator(
        task_id="rank_movies",
        python_callable=_rank_movies,
        templates_dict={
            "input_path": "/data/custom_sensor/ratings/{{ds}}.json",
            "output_path": "/data/custom_sensor/rankings/{{ds}}.csv",
        },
    )

    wait_for_ratings >> fetch_ratings >> rank_movies
