FROM python:3.8-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY scripts/fetch-ratings.py /usr/local/bin/fetch-ratings
RUN chmod +x /usr/local/bin/fetch-ratings # make script executable

# ensure that the script is on the PATH so that it can be run without
# specifying the full path to the script
ENV PATH="/usr/local/bin:${PATH}"
