import csv
import json
import pathlib


def write(obj, f_path):
    f_path = pathlib.Path(f_path)
    f_path.parent.mkdir(parents=True, exist_ok=True)
    match f_path.suffix:
        case ".csv":
            _write_csv(obj, f_path)
        case ".json":
            _write_json(obj, f_path)
        case _:
            raise ValueError(f"Unsupported file type {f_path.suffix}")


def _write_csv(records, f_path):
    records = iter(records)
    record_0 = next(records)
    with f_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows([record_0._fields, record_0])
        writer.writerows(records)


def _write_json(obj, f_path):
    with f_path.open("w") as f:
        json.dump(obj, f)


def read(f_path):
    f_path = pathlib.Path(f_path)
    match f_path.suffix:
        case ".json":
            return _read_json(f_path)
        case _:
            raise ValueError(f"Unsupported file type {f_path.suffix}")


def _read_json(f_path):
    with f_path.open("r") as f:
        return json.load(f)
