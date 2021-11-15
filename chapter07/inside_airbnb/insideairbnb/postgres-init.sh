#!/bin/bash

set -euxo pipefail

function create_user_and_database() {
    local database=$1
    echo "Creating user '$database' with database '$database'."

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER $database WITH PASSWORD '$database';
    CREATE DATABASE $database;
    GRANT ALL PRIVILEGES ON DATABASE $database TO $database;
EOSQL
}

# 1. create databases
create_user_and_database "insideairbnb"

# 2. Create table for insideairbnb listings
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" insideairbnb <<-EOSQL
CREATE TABLE IF NOT EXISTS listings(
  id                             INTEGER,
  name                           TEXT,
  host_id                        INTEGER,
  host_name                      VARCHAR(100),
  neighbourhood_group            VARCHAR(100),
  neighbourhood                  VARCHAR(100),
  latitude                       NUMERIC(18,16),
  longitude                      NUMERIC(18,16),
  room_type                      VARCHAR(100),
  price                          INTEGER,
  minimum_nights                 INTEGER,
  number_of_reviews              INTEGER,
  last_review                    DATE,
  reviews_per_month              NUMERIC(5,2),
  calculated_host_listings_count INTEGER,
  availability_365               INTEGER,
  download_date                  DATE NOT NULL
);
EOSQL

# 3. Download Inside Airbnb Amsterdam listings data (http://insideairbnb.com/get-the-data.html)
listing_url="http://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/{DATE}/visualisations/listings.csv"
listing_dates="
2021-07-04
2021-06-03
2021-05-19
2021-04-09
2021-03-04
2021-02-08
2021-01-09
2020-12-12
"
mkdir -p /tmp/insideairbnb

for d in ${listing_dates}
do
  url=${listing_url/\{DATE\}/$d}
  wget $url -O /tmp/insideairbnb/listing-$d.csv

  # use sed to remove the last csv column: - doesn't work correctly
#  sed -i "s/,[^,.]*$//" /tmp/insideairbnb/listing-$d.csv

  # Hacky way to add the "download_date", by appending the date to all rows in the downloaded file
  sed -i "1 s/$/,download_date/" /tmp/insideairbnb/listing-$d.csv
  sed -i "2,$ s/$/,$d/" /tmp/insideairbnb/listing-$d.csv

#  head -n 1 /tmp/insideairbnb/listing-$d.csv

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" insideairbnb <<-EOSQL
    COPY listings FROM '/tmp/insideairbnb/listing-$d.csv' DELIMITER ',' CSV HEADER QUOTE '"';
EOSQL
done

function grant_all() {
	local database=$1

  sleep 10;
	echo "GRANTING PERMISSIONS to '$database' with user '$POSTGRES_USER'"

	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" $database <<-EOSQL
    ALTER SCHEMA public OWNER TO $database;
    GRANT USAGE ON SCHEMA public TO $database;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $database;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $database;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $database;
EOSQL
}

# Somehow the database-specific privileges must be set AFTERWARDS
grant_all "insideairbnb"

pg_ctl stop
