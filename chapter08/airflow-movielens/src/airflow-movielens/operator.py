import json
from pathlib import Path
from typing import Any

from airflow.models import BaseOperator

from .movielens_hook import MovielensHook


class MovielensFetchRatingsOperators(BaseOperator):
    """Operator that fetches ratings from the Movielens API.

    Parameters
    ----------
    conn_id : str
        ID of the connection to use to connect to the Movielens
        API. Connection is expected to include authentication
        details (login/password) and the host that is serving the API.
        output_path : str
        Path to write the fetched ratings to.
    start_date : str
        (Templated) start date to start fetching ratings from (inclusive).
        Expected format is YYYY-MM-DD (equal to Airflow"s ds formats).
    end_date : str
        (Templated) end date to fetching ratings up to (exclusive).
        Expected format is YYYY-MM-DD (equal to Airflow"s ds formats).

    """

    template_fields = ["_start_date", "_end_date", "_output_path"]

    def __init__(
        self,
        conn_id,
        output_path,
        start_date="{{ds}}",
        end_date="{{next_ds}}",
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._conn_id = conn_id
        self._output_path = output_path
        self._start_date = start_date
        self._end_date = end_date

    def execute(self, context: Any):
        hook = MovielensHook(self._conn_id)

        try:
            self.log.info(
                f"Fetching ratings for {self._start_date} to {self._end_date}"
            )

            ratings = list(
                hook.get_ratings(start_date=self._start_date, end_date=self._end_date)
            )

            self.log.info(f"Fetched {len(ratings)} ratings.")
        finally:
            hook.close()

        self.log.info(f"Writing ratings to {self._output_path}")

        path = self._output_path[: self._output_path.rfind("/")]
        Path(path).mkdir(parents=True, exist_ok=True)

        with open(self._output_path, "w") as file:
            json.dump(ratings, file)
