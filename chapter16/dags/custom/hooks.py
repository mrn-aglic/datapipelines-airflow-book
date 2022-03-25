from datetime import datetime
from typing import Any

import requests
from airflow.hooks.base import BaseHook


class MovielensHook(BaseHook):
    DEFAULT_SCHEMA = "http"
    DEFAULT_PORT = "5010"

    def __init__(self, conn_id):
        super().__init__()
        self._conn_id = conn_id

        self._base_url = None
        self._session = None

    def get_conn(self) -> Any:
        """Returns the connection used by the hook for querying data. Should in principle not be used directly."""

        if not self._session:
            # fetch connection details from the metastore:
            config = self.get_connection(self._conn_id)

            if not config.host:
                raise ValueError(f"No host specified in connection {self._conn_id}")

            host = config.host

            schema = config.schema or self.DEFAULT_SCHEMA
            port = config.port or self.DEFAULT_PORT

            self._base_url = f"{schema}://{host}:{port}"

            self._session = requests.Session()

            if config.login:
                self._session.auth = (config.login, config.password)

        return self._session, self._base_url

    def close(self):
        """Closes any active session."""
        if self._session:
            self._session.close()
        self._session = None
        self._base_url = None

    ### Implemented for the use of Chapter09 where hook is used as a context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    ###

    def get_ratings(self, start_date=None, end_date=None, batch_size=100):
        """Fetches ratings between the given start/end date.

        Parameters
        ----------
        start_date : str
            Start date to start fetching ratings from (inclusive). Expected
            format is YYYY-MM-DD (equal to Airflow's ds formats).
        end_date : str
            End date to fetching ratings up to (exclusive). Expected
            format is YYYY-MM-DD (equal to Airflow's ds formats).
        batch_size : int
            Size of the batches (pages) to fetch from the API. Larger values
            mean less requests, but more data transferred per request.

        """

        yield from self._get_with_pagination(
            endpoint="/ratings",
            params={"start_date": start_date, "end_date": end_date},
            batch_size=batch_size,
        )

    def get_ratings_for_month(self, year, month, batch_size=100):
        """Fetches ratings for a given month.

        Parameters
        ----------
        year : int
            Year to fetch for.
        month : int
            Month to fetch for.
        batch_size : int
            Size of the batches (pages) to fetch from the API. Larger values
            mean less requests, but more data transferred per request.

        """
        start_date = datetime(year=year, month=month, day=1)

        if month == 12:
            end_date = datetime(year + 1, month=1, day=1)
        else:
            end_date = datetime(year, month=month + 1, day=1)

        yield from self.get_ratings(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            batch_size=batch_size,
        )

    def _get_with_pagination(self, endpoint, params, batch_size=100):
        """Fetches records using a GET request with given URL/params, taking pagination into account."""

        session, base_url = self.get_conn()

        offset = 0
        total = None

        url = f"{base_url}{endpoint}"

        while total is None or offset < total:
            response = session.get(
                url, params={**params, **{"offset": offset, "limit": batch_size}}
            )
            response.raise_for_status()
            response_json = response.json()

            yield from response_json["result"]

            offset += batch_size
            total = response_json["total"]
