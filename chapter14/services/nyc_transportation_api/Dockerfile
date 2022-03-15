FROM python:3.8-slim

COPY app.py requirements.txt /app/
COPY templates /app/templates
WORKDIR /app

RUN pip install -r requirements.txt
EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["app.py"]
