import os
from datetime import date

import psycopg2
import psycopg2.extras
from flask import Flask, Response, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {"citibike": generate_password_hash("cycling")}

sql_queries = {
    "default": lambda year_offset, amount, period: f"""
    SELECT  tripduration,
            starttime + INTERVAL '{year_offset} YEARS' as starttime,
            stoptime + INTERVAL '{year_offset} YEARS' as stoptime,
            start_station_id,
            start_station_name,
            start_station_latitude,
            start_station_longitude,
            end_station_id,
            end_station_name,
            end_station_latitude,
            end_station_longitude
    FROM tripdata
    WHERE stoptime + INTERVAL '{year_offset} YEARS' <= NOW() AND
            stoptime + INTERVAL '{year_offset} YEARS' >= NOW() - INTERVAL '{amount} {period}s'
    """
}


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None


@app.route("/")
@auth.login_required
def index():
    return "Welcome to citibike {user}".format(user=auth.current_user())


def _get_connection():
    return psycopg2.connect(
        database=os.environ["POSTGRES_DATABASE"],
        user=os.environ["POSTGRES_USERNAME"],
        host=os.environ["POSTGRES_HOST"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


@app.route("/recent/<period>", defaults={"amount": 1}, methods=["GET"])
@app.route("/recent/<period>/<amount>", methods=["GET"])
@auth.login_required
def get_recent_rides(period: str, amount: str):
    """Return

    :param period: either "minute", "hour", or "day"
    :param amount: (optional) the number of periods
    :return:
    """

    if period not in ("minute", "hour", "day"):
        return Response("Period can only be 'minute', 'hour', or 'day'!", status=422)

    year_offset = date.today().year - int(os.environ["DATA_YEAR"])
    conn = _get_connection()

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        query = sql_queries["default"](year_offset, amount, period)
        cursor.execute(query)
        data = cursor.fetchall()

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
