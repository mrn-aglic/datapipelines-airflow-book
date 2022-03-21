import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import click
import pandas as pd

logging.basicConfig(
    format="[%(asctime)-15s] %(levelname)s - %(message)s", level=logging.INFO
)


# Movielens dataset was generated on November 21, 2019.
# These data were created by 162541 users between January 09, 1995 and November 21, 2019.
@click.command()
@click.option("--start_date", default="2019-01-01", type=click.DateTime())
@click.option("--end_date", default="2020-01-01", type=click.DateTime())
@click.option("--output_path", required=True)
def main(start_date, end_date, output_path):
    """Script for fetching movielens ratings within a given date range."""

    logging.info("Fetching ratings...")
    ratings = fetch_ratings()

    # Subset to expected range.
    logging.info("Filtering for dates %s - %s...", start_date, end_date)
    ts_parsed = pd.to_datetime(ratings["timestamp"], unit="s")
    ratings = ratings.loc[(ts_parsed >= start_date) & (ts_parsed < end_date)]

    logging.info("Writing ratings to '%s'...", output_path)
    ratings.to_csv(output_path, index=False)


def fetch_ratings():
    """Fetches ratings from the given URL."""

    url = "https://files.grouplens.org/datasets/movielens/ml-25m.zip"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir, "download.zip")
        logging.info("Downloading zip file from %s", url)
        urlretrieve(url, tmp_path)

        with zipfile.ZipFile(tmp_path) as zip_:
            logging.info("Downloaded zip file with contents: %s", zip_.namelist())

            logging.info("Reading ml-25m/ratings.csv from zip file")
            with zip_.open("ml-25m/ratings.csv") as file_:
                ratings = pd.read_csv(file_)

    return ratings


if __name__ == "__main__":
    main()
