import csv
import json
from pathlib import Path

from airflowbook.json_to_csv_operator import JsonToCsvOperator


def test_json_to_csv_operator(tmp_path: Path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.csv"

    # Write input data to tmp path
    input_data = [
        {"name": "bob", "age": "41", "sex": "M"},
        {"name": "alice", "age": "24", "sex": "F"},
        {"name": "carol", "age": "60", "sex": "F"},
    ]

    with open(input_path, "w") as f:
        json.dump(input_data, f)

    operator = JsonToCsvOperator(
        task_id="test", input_path=input_path, output_path=output_path
    )

    operator.execute(context={})

    with open(output_path, "r") as f:
        reader = csv.DictReader(f)
        result = [dict(row) for row in reader]

    assert result == input_data