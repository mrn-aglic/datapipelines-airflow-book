#!/bin/bash

ECHO "Deleting previous data subfolders"
docker exec chapter06_scheduler_1 sh -c "rm -r /data/*"
docker exec chapter06_scheduler_1 sh -c "ls /data"

echo "Done deleting..."

echo "Creating new subfolders and copying data..."

for VARIABLE in 1 2 3 4
do
  docker exec chapter06_scheduler_1 sh -c "mkdir -p /data/supermarket${VARIABLE}"
  docker cp ../data/. chapter06_scheduler_1:/data/supermarket${VARIABLE}/
done

echo "Done. Check ls output"
docker exec chapter06_scheduler_1 sh -c "ls -R /data"
