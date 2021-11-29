import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from custom.ranking import rank_movies_by_rating

MOVIELENS_HOST = os.environ.get("MOVIELENS_HOST", "movielens-api")
MOVIELENS_SCHEMA = os.environ.get("MOVIELENS_SCHEMA", "http")
MOVIELENS_PORT = os.environ.get("MOVIELENS_PORT", "5010")

MOVIELENS_USER = os.environ["MOVIELENS_USER"]
MOVIELENS_PASSWORD = os.environ["MOVIELENS_PASSWORD"]


def _get_session():
    """Builds a requests Session for the Movielens API."""
    session = requests.Session()
    session.auth = (MOVIELENS_USER, MOVIELENS_PASSWORD)

    base_url = f"{MOVIELENS_SCHEMA}://{MOVIELENS_HOST}:{MOVIELENS_PORT}"

    return session, base_url


def _get_with_pagination(session, url, params, batch_size=100):
    """Fetches records using a GET request with given URL/params, taking pagination into account."""

    offset = 0
    total = None

    while total is None or offset < total:
        response = session.get(
            url, params={**params, **{"offset": offset, "limit": batch_size}}
        )
        response.raise_for_status()
        response_json = response.json()

        yield from response_json["result"]

        offset += batch_size
        total = response_json["total"]


def _get_ratings(start_date, end_date, batch_size=100):
    session, base_url = _get_session()

    yield from _get_with_pagination(
        session=session,
        url=f"{base_url}/ratings",
        params={"start_date": start_date, "end_date": end_date},
        batch_size=batch_size,
    )


def _fetch_ratings(templates_dict: dict, batch_size=1000, **_):
    logger = logging.getLogger(__name__)

    start_date = templates_dict["start_date"]
    end_date = templates_dict["end_date"]
    output_path = templates_dict["output_path"]

    logger.info("Fetching ratings for %s to %s", start_date, end_date)

    ratings = list(
        _get_ratings(start_date=start_date, end_date=end_date, batch_size=batch_size)
    )
    logger.info("Fetched %s ratings.", len(ratings))

    logger.info("Writing ratings to %s", output_path)

    path = output_path[: output_path.rfind("/")]
    Path(path).mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as file:
        json.dump(ratings, file)


def _rank_movies(templates_dict, min_ratings=2, **_):
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
    dag_id="01_fetch_ratings_python", start_date=datetime(2019, 1, 1), max_active_runs=1
) as dag:
    fetch_ratings = PythonOperator(
        task_id="fetch_ratings",
        python_callable=_fetch_ratings,
        templates_dict={
            "start_date": "{{ds}}",
            "end_date": "{{next_ds}}",
            "output_path": "/data/python/ratings/{{ds}}.json",
        },
    )

    rank_movies = PythonOperator(
        task_id="rank_movies",
        python_callable=_rank_movies,
        templates_dict={
            "input_path": "/data/python/ratings/{{ds}}.json",
            "output_path": "/data/python/rankings/{{ds}}.csv",
        },
    )

    fetch_ratings >> rank_movies
