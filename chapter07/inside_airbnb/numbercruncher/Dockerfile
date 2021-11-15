FROM continuumio/miniconda3

RUN pip install pandas minio

ENV S3_ACCESS_KEY=user
ENV S3_SECRET_KEY=password
ENV S3_ENDPOINT=locals3:9000

COPY crunchdata.py /root/crunchdata.py

ENTRYPOINT ["python"]
CMD ["/root/crunchdata.py"]
