import pickle


def write(obj, f_path):
    f_path.parent.mkdir(parents=True, exist_ok=True)
    if f_path.suffix == ".pickle":
        _write_pickle(obj, f_path)
    else:
        raise ValueError(f"Unsupported file type {f_path.suffix}")


def _write_pickle(obj, f_path):
    with f_path.open("wb") as f:
        pickle.dump(obj, f)


def read(f_path):
    if f_path.suffix == ".pickle":
        return _read_pickle(f_path)
    else:
        raise ValueError(f"Unsupported file type {f_path.suffix}")


def _read_pickle(f_path):
    with f_path.open("rb") as f:
        return pickle.load(f)
