FROM python:3.8-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY scripts/fetch_weather.py /usr/local/bin/fetch-weather
RUN chmod +x /usr/local/bin/fetch-weather # make script executable

ENTRYPOINT ["/usr/local/bin/fetch-weather"]
CMD ["--help"]
