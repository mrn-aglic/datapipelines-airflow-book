FROM postgres:11.1-alpine

COPY postgres-init.sql /docker-entrypoint-initdb.d/postgres-init.sql

EXPOSE 5432
CMD ["postgres"]
