import csv
import pathlib


def write(obj, f_path):
    f_path = pathlib.Path(f_path)
    f_path.parent.mkdir(parents=True, exist_ok=True)
    match f_path.suffix:
        case ".csv":
            _write_csv(obj, f_path)
        case _:
            raise ValueError(f"Unsupported file type {f_path.suffix}")


def _write_csv(records, f_path):
    records = iter(records)
    record_0 = next(records)
    with f_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows([record_0._fields, record_0])
        writer.writerows(records)


def read(record_type, f_path):
    f_path = pathlib.Path(f_path)
    match f_path.suffix:
        case ".csv":
            return _read_csv(record_type, f_path)
        case _:
            raise ValueError(f"Unsupported file type {f_path.suffix}")


def _read_csv(record_type, f_path):
    with f_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames
        if tuple(reader.fieldnames) != record_type._fields:
            raise ValueError(
                f"Record type {record_type} with fields {record_type._fields} not consistent with records in {f_path} ({reader.fieldnames})"
            )
        return [record_type(**record) for record in reader]
