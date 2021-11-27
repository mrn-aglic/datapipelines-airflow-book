# The function implemented in this script is later used in an actual DAG.
# Hence python_scripts directory is not a service in the full docker-compose and can
# be ignored completely

import os

import requests

MOVIELENS_HOST = os.environ.get("MOVIELENS_HOST", "localhost")
MOVIELENS_SCHEMA = os.environ.get("MOVIELENS_SCHEMA", "http")
MOVIELENS_PORT = os.environ.get("MOVIELENS_PORT", "5010")

MOVIELENS_USER = os.environ.get("MOVIELENS_USER", "airflow")
MOVIELENS_PASSWORD = os.environ.get("MOVIELENS_PASSWORD", "airflow")


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


ratings = _get_ratings("2019-01-01", "2019-01-02")
single = next(ratings)

print(f"single: {single}")
print(f"all: {list(ratings)}")
