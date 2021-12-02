# NOTE: this docker container is only for demonstrating the script fetchig_ratings_api
# it is not included as a service in the docker-compose.py

FROM python:3.8-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm -rf /tmp/requirements.txt

COPY fetching_ratings_api.py /

CMD ["python", "/fetching_ratings_api.py"]
