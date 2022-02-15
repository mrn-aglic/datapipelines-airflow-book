#!/bin/bash

set -eux

YEAR="2020"

# Create database
psql -v ON_ERROR_STOP=1 <<-EOSQL
  CREATE DATABASE citibike;
EOSQL

# Create table
psql -v ON_ERROR_STOP=1 citibike <<-EOSQL
  CREATE TABLE IF NOT EXISTS tripdata (
    tripduration            INTEGER,
    starttime               TIMESTAMP,
    stoptime                TIMESTAMP,
    start_station_id        INTEGER,
    start_station_name      VARCHAR(70),
    start_station_latitude  FLOAT8,
    start_station_longitude FLOAT8,
    end_station_id          INTEGER,
    end_station_name        VARCHAR(70),
    end_station_latitude    FLOAT8,
    end_station_longitude   FLOAT8
  );
EOSQL

# Load data
urls="
https://s3.amazonaws.com/tripdata/${YEAR}01-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}02-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}03-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}04-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}05-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}06-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}07-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}08-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}09-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}10-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}11-citibike-tripdata.csv.zip
https://s3.amazonaws.com/tripdata/${YEAR}12-citibike-tripdata.csv.zip
"

for url in ${urls}
do
  wget "${url}" -O /tmp/citibike-tripdata.csv.zip # Download data
  unzip /tmp/citibike-tripdata.csv.zip -d /tmp # Unzip
  filename=$(echo ${url} | sed 's:.*/::' | sed 's/\.zip$//') # Determine filename of unzipped CSV (this is the same as the .zip file)
  # Filter lines otherwise full Docker image is 4.18GB, every 8th line results in 890MB
  time awk -F',' 'NR == 1 || NR % 8 == 0 {print $1","$2","$3","$4","$5","$6","$7","$8","$9","$10","$11}' /tmp/${filename} | grep -v "NULL" > /tmp/citibike-tripdata.csv # Extract specific columns, write result to new file
  time psql -v ON_ERROR_STOP=1 citibike <<-EOSQL
    COPY tripdata
    FROM '/tmp/citibike-tripdata.csv' DELIMITER ',' CSV HEADER;
EOSQL
done

psql -v ON_ERROR_STOP=1 <<-EOSQL
  CREATE USER city WITH PASSWORD 'cycling';
  GRANT ALL PRIVILEGES ON DATABASE citibike TO city;
  \c citibike;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO city;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO city;
EOSQL

pg_ctl stop
