current_dir = $(shell pwd)

build-tests:
	docker build -t airflow-book-tests:latest airflow-test-docker

run-tests:
	docker run -v $(current_dir)/dags/:/dags -v $(current_dir)/tests/:/tests airflow-book-tests

start-tests:
	make build-tests && make run-tests
