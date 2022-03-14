# Chapter 14

## Main question
How to get from point A to B in NYC as fast as possible?

## Mini project structure
1. A rest API for serving City Bike data
2. One file share serving Yellow Cab taxi data
3. MinIO, an object store that supports the S3 protoclo (
   see chapter 07)
4. PostgreSQL database for querying and storing data
5. A Flask application displaying the results

## Data endpoints
The data is available on the following endpoints:
1. Yellow Cab data: http://localhost:8081
2. Citi Bike data: http://localhost:8082

## My implementation steps
1. taxi_db - pull the data from s3 online storage and store it to
postgresql database (see notes below). Connect to db directly with
user: taxi, password: ridetlc. Database name: `tlctriprecords`.
Run service with: `docker-compose up taxi_db`.
2. taxi_fileserver - serves the data from the taxi_db data dataset
as csv files. Run service with: `docker-compose up taxi_fileserver`.
3. citibike_db - pull the data from s3 online storage and store it to
postgresql database (see notes below). Connect to db directly with
user: citi, password: cycling. Database name: `citibike`.
Run service with: `docker-compose up citibike_db`.
4. citibike_api - pretty straightforward. Note that the SQL query
includes an offset so that we simulate data for each year.
Run service with:`docker-compose up citibike_api`.
5. minio (minio-s3) and minio/mc - run together with:
`docker-compose up minio-s3 minio_init` (see notes below).
6. implementing the first DAG and download citibike data task.
Implementing the download taxi data task.
7. Implementing the PandasOperator in a separate package called
nyctransport (directory nyc_operators)
8. Implementing minio_helpers - the get_minio_object and
write_minio object operators
9. Used the functions developed in points 7 and 8 to write
the `transform_taxi_data` operator (without the
transform function).
10. Implemented the transform data function for the taxi data.
11. Implemented the the `transform_citibike_data` operator.
12. Add the `result_db` service to ensure we have a place to store
the results of the transformations.
13. Implement the S3 to postgres operator in the separate package.


### Taxi_db notes
I like using with newish things. So I looked up the availability
of the data for 2021. But at the time of writing, the data for
2021 is available up to July. To keep things simple, I'm gonna
use the data from 2020.
Just like the author states in the GitHub repo for the book,
the docker image will become very large if we take all of the
data. Therefore, data is taken only every X lines.

### Taxi_fileserver notes
serves the data from the taxi_db data dataset
as csv files. The index `localhost:8081` returns the list of
available csvs. Two scripts generate the csv files:
   - `get_last_hour.sh` generates the csv containing the data
   "for the last 15 minutes". Note that the year may is different.
   The script is run every 15 minutes and deletes csv files
   older than an hour.
   - `get_last_hour_reboot.sh` is called when the system is
   rebooted to generate csvs that we can use.

The available file can be accessed via `localhost:8081/filename`.

### Citibike_db notes
As for taxi_db, the data is loaded for the year 2020.

### Minio and minio mc notes
To enable these services. you first need to copy .env_backup
to .env. Enter the root user and root password information
and start up minio with `docker-compose up minio_s3`. Then login
into the minio service on port `localhost:9000` and create a service
account. Copy and paste the access and secret keys into the .env file
variables MC_ACCESS_KEY and MC_SECRET_KEY. You can stop
the minio service now.

You can also rename the bucket that is created with the mc client.
The name of the bucket is stored in the BUCKET_NAME environment
variable in docker-compose.

You can start both minio and minio mc using:
`docker-compose up minio-s3 minio_init`.

### Airflow Notes
Airflow services use the `chapter14/.env` file for "secrets". For example, the .env file contains
the following environment variables:
- `AIRFLOW_CONN_CITIBIKE`: citibike api url with credentials (since these are in sh, I made no attempt
to hide them). However, they definitely should be a secret in production systems.
- `AIRFLOW_CONN_S3`: the connection for minio. I reused the access and secret keys from Minio MC
for this connection id. Note that the connection has to be URL escaped, e.g.:

   `AIRFLOW_CONN_S3=s3://<access_key>:<secret_key>@?host=http%3A%2F%2Fminio-s3%3A9000`

Copy the .env_backup file and fill in the missing values.


### Separate package
As part of point 7, the PandasOperator is implemented as a separate
package and installed in the docker image during docker build.
The source for the package is included in this project
as a git submodule. You can navigate to the repo of the package.
