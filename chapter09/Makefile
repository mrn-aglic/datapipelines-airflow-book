current_dir = $(shell pwd)
bridge_name = chapter08_default # substitute with the network name that your
# docker-compose services from chapter08 are using.

build-tests:
	docker build -t airflow-book-tests:latest airflow-test-docker

build-tests-nc:
	docker build --no-cache -t airflow-book-tests:latest airflow-test-docker

run-tests:
	docker run --net=$(bridge_name) -v $(current_dir)/dags/:/dags -v $(current_dir)/tests/:/tests airflow-book-tests

start-tests:
	make build-tests && make run-tests
