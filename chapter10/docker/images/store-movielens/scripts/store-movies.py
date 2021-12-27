#!/usr/bin/env python

import logging

import click
import pandas as pd
from psycopg2 import connect

logging.basicConfig(level=logging.INFO)


@click.command()
@click.option(
    "--input_path",
    type=click.Path(dir_okay=False, exists=True, readable=True),
    required=True,
)
@click.option("--user", required=True)
@click.option("--password", required=True)
@click.option("--host", required=True)
@click.option("--port", required=True)
@click.option("--date", required=True)
def main(input_path, user, password, host, port, date):
    """CLI script for fetching movie ratings from the movielens API."""

    data = pd.read_csv(input_path)
    insert_query = (
        "INSERT INTO movielens (movieId, avg_rating, num_ratings, scrapeTime) "
        "VALUES ({0}, '{1}')"
    )

    with connect(user=user, password=password, host=host, port=port) as conn:
        cursor = conn.cursor()

        values = [k[1].values.tolist() for k in data.iterrows()]

        insert_queries = [
            insert_query.format(",".join(str(el) for el in row), date) for row in values
        ]

        for query in insert_queries:
            cursor.execute(query)

        cursor.execute("SELECT COUNT(*) FROM movielens")
        num_rows_inserted = cursor.fetchone()[0]
        print(f"Num rows inserted: {num_rows_inserted}")


if __name__ == "__main__":
    main()
