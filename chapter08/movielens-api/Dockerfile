FROM python:3.8-slim

COPY requirements.in /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm -rf /tmp/requirements.txt

COPY app.py fetch_ratings.py /
RUN python /fetch_ratings.py --output_path /ratings.csv

EXPOSE 5010

ENTRYPOINT ["python"]
CMD ["/app.py"]
