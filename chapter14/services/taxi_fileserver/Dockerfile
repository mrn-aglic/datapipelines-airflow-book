FROM nginx:1.21-alpine

# Fixed variable used to offset dates returned by the taxi fileserver to the current year,
ENV DATA_YEAR=2020

RUN apk update && \
    apk add postgresql-client && \
    mkdir /data

COPY get_last_hour.sh /etc/periodic/15min/get_last_hour
COPY get_last_hour_reboot.sh /usr/local/bin/get_last_hour_reboot

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /etc/periodic/15min/get_last_hour && \
    chmod +x /usr/local/bin/get_last_hour_reboot && \
    chmod +x /entrypoint.sh && \
    echo "@reboot /usr/local/bin/get_last_hour_reboot" >> /etc/crontabs/root

ENTRYPOINT ["/entrypoint.sh"]
