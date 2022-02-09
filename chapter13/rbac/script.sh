docker exec -it ch13_rbac_webserver airflow users create \
  --role Admin \
  --username test \
  --password topsecret \
  --email test@test.com \
  --firstname mr \
  --lastname test
