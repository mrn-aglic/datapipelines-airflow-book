# Chapter 12

Make sure that your local docker has can have at least of 4 GB of
RAM. My setup has access to 5 GB. This can be setup in Docker
dashboard -> settings -> resources panel.

When working with Grafana (chapter 12.4.4) there are a few things
that should be different than in the book. If Grafana is running
as part of docker-compose, the Prometheus url entered when
creating a data source should be `http://prometheus:9090`as
opposed to `http://localhost:9090` as mentioned in the book.

Additionally, the book suggests you add the metric
`airflow_dag_processing_total_parse_time` for the first
dashboard. Note that this metric has a different name in this
repository: `airflow_dag_processing_total_time`.
