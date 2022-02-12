FROM python:3.9-slim

RUN pip install Flask
COPY app.py /app/app.py
RUN chmod +x /app/app.py

EXPOSE 5010

ENTRYPOINT ["python"]
CMD ["/app/app.py"]
