FROM python:3.8-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY scripts/rank-movies.py /usr/local/bin/rank-movies
RUN chmod +x /usr/local/bin/rank-movies

# ensure that the script is on the PATH so that it can be run without
# specifying the full path to the script
ENV PATH="/usr/local/bin:${PATH}"
