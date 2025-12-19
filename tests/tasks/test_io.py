import collections

import pytest

from tasks import io


def test_round_trip_csv(tmp_path):
    Record = collections.namedtuple("Record", ["name"])
    f_path = tmp_path / "subdir" / "records.csv"
    records = [Record("name_a"), Record("name_b")]

    io.write(records, f_path)
    assert f_path.read_text() == "name\n" + "name_a\n" + "name_b\n"

    assert io.read(Record, f_path) == records


def test_write_unsupported_file_type(tmp_path):
    f_path = tmp_path / "subdir" / "obj.json"
    with pytest.raises(ValueError):
        io.write({"my_key": "my_value"}, f_path)
    assert f_path.parent.exists()  # This is undesirable


def test_read_unsupported_file_type(tmp_path):
    f_path = tmp_path / "subdir" / "obj.json"
    with pytest.raises(ValueError):
        io.read(None, f_path)


def test_read_wrong_record_format(tmp_path):
    f_path = tmp_path / "records.csv"

    OldRecord = collections.namedtuple("Record", ["name"])
    records = [OldRecord("name_a"), OldRecord("name_b")]
    io.write(records, f_path)

    NewRecord = collections.namedtuple("Record", ["other_field"])
    with pytest.raises(ValueError):
        io.read(NewRecord, f_path)
