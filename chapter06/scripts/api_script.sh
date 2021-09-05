curl -X POST "http://localhost:8080/api/v1/dags/07_print_dag_run_conf/dagRuns" -H  "Content-Type: application/json" -d '{"conf": {"supermarket": 1}}' --user "user:password"
