openssl req -x509 -newkey rsa:4096 -sha256 -nodes -days 365 \
-keyout certs/privatekey.pem \
-out certs/certificate.pem \
-extensions san \
-config openssl.conf \
-subj "/CN=localhost"
