import csv
import itertools
import json
import pickle


def write(obj, f_path):
    f_path.parent.mkdir(parents=True, exist_ok=True)
    if f_path.suffix == ".pickle":
        _write_pickle(obj, f_path)
    elif f_path.suffix == ".csv":
        _write_csv(obj, f_path)
    elif f_path.suffix == ".json":
        _write_json(obj, f_path)
    else:
        raise ValueError(f"Unsupported file type {f_path.suffix}")


def _write_pickle(obj, f_path):
    with f_path.open("wb") as f:
        pickle.dump(obj, f)


def _write_csv(records, f_path):
    records = iter(records)
    record_0 = next(records)
    with f_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(itertools.chain([record_0._fields], [record_0], records))


def _write_json(obj, f_path):
    with f_path.open("w") as f:
        json.dump(obj, f, indent=2)


def read(f_path):
    if f_path.suffix == ".pickle":
        return _read_pickle(f_path)
    elif f_path.suffix == ".json":
        return _read_json(f_path)
    else:
        raise ValueError(f"Unsupported file type {f_path.suffix}")


def _read_pickle(f_path):
    with f_path.open("rb") as f:
        return pickle.load(f)


def _read_json(f_path):
    with f_path.open("r") as f:
        return json.load(f)
