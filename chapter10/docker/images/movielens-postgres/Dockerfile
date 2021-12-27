FROM postgres:latest

COPY postgres-init.sql /docker-entrypoint-initdb.d/postgres-init.sql

EXPOSE 5432
CMD ["postgres"]
