import json

import geopandas
import pandas as pd
import requests
from airflow import DAG
from airflow.hooks.base import BaseHook
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.dates import days_ago
from flask_httpauth import HTTPBasicAuth
from nyctransport.operators.pandas_operator import PandasOperator
from shared.minio_helpers import get_minio_object, write_minio_object


def _download_taxi_data():
    taxi_conn = BaseHook.get_connection(conn_id="taxi")

    s3_hook = S3Hook(aws_conn_id="s3")

    url = f"http://{taxi_conn.host}"
    response = requests.get(url)
    files = response.json()

    exported_files = []

    for filename in [f["name"] for f in files]:
        response = requests.get(f"{url}/{filename}")
        s3_key = f"raw/taxi/{filename}"
        try:
            s3_hook.load_string(
                string_data=response.text,
                key=s3_key,
                bucket_name=Variable.get("MC_BUCKET_NAME"),
            )
            print(f"Uplaoded file {s3_key} to Minio.")
            exported_files.append(s3_key)
        except ValueError:
            print(f"File {s3_key} already exists.")

    return exported_files


def _transform_taxi_data(df):
    df[["picku_datetime", "dropoff_datetime"]] = df[
        ["pickup_datetime", "dropoff_datetime"]
    ].apply(pd.to_datetime)

    df["tripduration"] = (
        (df["dropoff_datetime"] - df["pickup_datetime"]).dt.total.seconds().astype(int)
    )

    df = df.rename(
        columns={
            "pickup_datetime": "starttime",
            "pickup_locationid": "start_location_id",
            "dropoff_datetime": "stoptime",
            "dropoff_locationid": "end_location_id",
        }
    ).drop(columns=["trip_distance"])

    return df


def _download_citibike_data(ts_nodash, **_):
    citibike_conn = BaseHook.get_connection(conn_id="citibike")

    url = f"http://{citibike_conn.host}:{citibike_conn.port}/recent/minute/15"
    response = requests.get(
        url, auth=HTTPBasicAuth(citibike_conn.login, citibike_conn.password)
    )

    data = response.json()

    s3_hook = S3Hook(aws_conn_id="s3")
    s3_key = f"raw/citibike/{ts_nodash}.json"
    try:
        s3_hook.load_string(
            string_data=json.dumps(data),
            key=s3_key,
            bucket_name=Variable.get("MC_BUCKET_NAME"),
        )
        print(f"Uploaded file {s3_key}")
    except ValueError:
        print(f"File {s3_key} already exists.")


def _transform_citibike_data(df):
    # Map citi bike lat,lon coordinates to taxi zone ids
    taxi_zones = geopandas.read_file(
        "https://s3.amazonaws.com/nyc-tlc/misc/taxi_zones.zip"
    ).to_crs("EPSG:4326")
    start_gdf = geopandas.GeoDataFrame(
        df,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(
            df["start_station_longitude"], df["start_station_latitude"]
        ),
    )
    end_gdf = geopandas.GeoDataFrame(
        df,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(
            df["end_station_longitude"], df["end_station_latitude"]
        ),
    )
    df_with_zones = geopandas.sjoin(
        start_gdf, taxi_zones, how="left", op="within"
    ).rename(columns={"LocationID": "start_location_id"})

    end_zones = geopandas.sjoin(end_gdf, taxi_zones, how="left", op="within")

    df_with_zones["end_location_id"] = end_zones["LocationID"]

    return df_with_zones[
        [
            "tripduration",
            "starttime",
            "start_location_id",
            "stoptime",
            "end_location_id",
        ]
    ]


dag = DAG(
    dag_id="nyc_dag",
    start_date=days_ago(1),
    schedule_interval="*/15 * * * *",
    catchup=False,
)

download_taxi_data = PythonOperator(
    task_id="download_taxi_data", python_callable=_download_taxi_data, dag=dag
)

transform_taxi_data = PandasOperator(
    task_id="process_taxi_data",
    input_callable=get_minio_object,
    input_callable_kwargs={
        "pandas_read_callable": pd.read_csv,
        "bucket": Variable.get("MC_BUCKET_NAME"),  # os.environ["MC_BUCKET_NAME"],
        "paths": "{{ ti.xcom_pull(task_ids='taxi_extract_transform.download_taxi_data') }}",
    },
    transform_callable=_transform_taxi_data,
    output_callable=write_minio_object,
    output_callable_kwargs={
        "bucket": Variable.get("MC_BUCKET_NAME"),  # os.environ["MC_BUCKET_NAME"],
        "path": "processed/taxi/{{ ts_nodash }}.parquet",
        "pandas_write_callable": pd.DataFrame.to_parquet,
        "pandas_write_callable_kwargs": {"engine": "auto"},
    },
)

download_citibike_data = PythonOperator(
    task_id="download_citibike_data", python_callable=_download_citibike_data, dag=dag
)
transform_citibike_data = PandasOperator(
    task_id="process_citibike_data",
    input_callable=get_minio_object,
    input_callable_kwargs={
        "pandas_read_callable": pd.read_csv,
        "bucket": Variable.get("MC_BUCKET_NAME"),  # os.environ["MC_BUCKET_NAME"],
        "paths": "{{ ti.xcom_pull(task_ids='taxi_extract_transform.download_taxi_data') }}",
    },
    transform_callable=_transform_citibike_data,
    output_callable=write_minio_object,
    output_callable_kwargs={
        "bucket": Variable.get("MC_BUCKET_NAME"),  # os.environ["MC_BUCKET_NAME"],
        "path": "processed/taxi/{{ ts_nodash }}.parquet",
        "pandas_write_callable": pd.DataFrame.to_parquet,
        "pandas_write_callable_kwargs": {"engine": "auto"},
    },
)

download_taxi_data >> transform_taxi_data
download_citibike_data >> transform_citibike_data
