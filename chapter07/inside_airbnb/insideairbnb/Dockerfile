FROM postgres:14-alpine AS builder

#ENV POSTGRES_HOST_AUTH_METHOD=trust
#ENV POSTGRES_USER="insideairbnb"
ENV POSTGRES_PASSWORD="insideairbnb"

COPY postgres-init.sh /docker-entrypoint-initdb.d/postgres-init.sh


RUN mkdir -p /data && \
    /usr/local/bin/docker-entrypoint.sh postgres || true && \
    cp -R /var/lib/postgresql/data/* /data


FROM postgres:14-alpine
COPY --from=builder /data /var/lib/postgresql/data
