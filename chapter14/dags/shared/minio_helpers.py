import io

import pandas as pd
from airflow.hooks.base import BaseHook
from minio import Minio


def get_minio_object(
    pandas_read_callable, bucket, paths, pandas_read_callable_kwargs=None
):
    s3_conn = BaseHook.get_connection(conn_id="s3")

    print(paths)

    minio_client = Minio(
        s3_conn.extra_dejson["host"].split("://")[1],
        access_key=s3_conn.login,
        secret_key=s3_conn.password,
        secure=False,
    )

    if isinstance(paths, str):
        paths = [paths]

    if pandas_read_callable_kwargs is None:
        pandas_read_callable_kwargs = {}

    dfs = []

    for path in paths:
        minio_object = minio_client.get_object(bucket_name=bucket, object_name=path)

        df = pandas_read_callable(minio_object, **pandas_read_callable_kwargs)

        dfs.append(df)

    return pd.concat(dfs)


def write_minio_object(
    df, pandas_write_callable, bucket, path, pandas_write_callable_kwargs=None
):
    s3_conn = BaseHook.get_connection(conn_id="s3")

    minio_client = Minio(
        s3_conn.extra_dejson["host"].split("://")[1],
        access_key=s3_conn.login,
        secret_key=s3_conn.password,
        secure=False,
    )

    bytes_buffer = io.BytesIO()
    pandas_write_method = getattr(
        df, pandas_write_callable.__name__
    )  # get reference to the DataFrame writing method
    pandas_write_method(bytes_buffer, **pandas_write_callable_kwargs)

    # make the function idempotent (useful when testing)
    # minio_client.remove_object(bucket_name=bucket, object_name=path)

    nbytes = bytes_buffer.tell()
    bytes_buffer.seek(0)

    minio_client.put_object(
        bucket_name=bucket,
        object_name=path,
        length=nbytes,
        data=bytes_buffer,
    )
