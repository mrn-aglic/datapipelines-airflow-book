FROM python:3.8-slim

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY scripts/store-movies.py /usr/local/bin/store-movies
RUN chmod +x /usr/local/bin/store-movies

ENV PATH="/usr/local/bin:${PATH}"
