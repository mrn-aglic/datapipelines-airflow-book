FROM postgres:14-alpine AS builder

#ENV POSTGRES_HOST_AUTH_METHOD=trust
ENV POSTGRES_PASSWORD=super_sercret_password

COPY postgres-init.sh /docker-entrypoint-initdb.d/postgres-init.sh

RUN apk update && \
    apk add ca-certificates && \
    update-ca-certificates && \
    mkdir -p /data && \
    /usr/local/bin/docker-entrypoint.sh postgres || true && \
    cp -R /var/lib/postgresql/data/* /data


FROM postgres:14-alpine
COPY --from=builder /data /var/lib/postgresql/data
ENV DATA_YEAR=2020
