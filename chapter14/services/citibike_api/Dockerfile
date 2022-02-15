FROM python:3.8-slim

COPY app.py requirements.txt /app/
WORKDIR /app

RUN pip install -r requirements.txt
EXPOSE 5010

ENTRYPOINT ["python"]
CMD ["app.py"]
