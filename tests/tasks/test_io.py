import collections

import pytest

from tasks import io


@pytest.mark.parametrize("suffix", [".pickle", ".json"])
def test_one_record_per_file(tmp_path, suffix):
    f_path = tmp_path / "subdir" / f"obj{suffix}"
    io.write({"my_key": "my_value"}, f_path)
    obj = io.read(f_path)
    assert obj == {"my_key": "my_value"}


def test_many_records_per_file(tmp_path):
    Record = collections.namedtuple("Record", ["name"])
    f_path = tmp_path / "subdir" / "records.csv"
    io.write([Record("name_a"), Record("name_b")], f_path)
    assert f_path.read_text() == "name\n" + "name_a\n" + "name_b\n"


def test_write_unsupported_file_type(tmp_path):
    f_path = tmp_path / "subdir" / "obj.txt"
    with pytest.raises(ValueError):
        io.write({"my_key": "my_value"}, f_path)
    assert f_path.parent.exists()  # This is undesirable


@pytest.mark.parametrize(
    "overwrite,value", [(True, "my_new_value"), (False, "my_value")]
)
def test_overwrite_if_exists(tmp_path, overwrite, value):
    f_path = tmp_path / "subdir" / "obj.json"
    io.write({"my_key": "my_value"}, f_path)
    io.write({"my_key": value}, f_path, overwrite_if_exists=overwrite)
    obj = io.read(f_path)
    assert obj == {"my_key": value}


def test_read_unsupported_file_type(tmp_path):
    f_path = tmp_path / "subdir" / "obj.txt"
    with pytest.raises(ValueError):
        io.read(f_path)
