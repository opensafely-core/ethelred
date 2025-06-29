import pytest

from tasks import io


def test_pickle(tmp_path):
    f_path = tmp_path / "subdir" / "obj.pickle"
    io.write({"my_key": "my_value"}, f_path)
    obj = io.read(f_path)
    assert obj == {"my_key": "my_value"}


def test_write_unsupported_file_type(tmp_path):
    f_path = tmp_path / "subdir" / "obj.txt"
    with pytest.raises(ValueError):
        io.write({"my_key": "my_value"}, f_path)
    assert f_path.parent.exists()  # This is undesirable


def test_read_unsupported_file_type(tmp_path):
    f_path = tmp_path / "subdir" / "obj.txt"
    with pytest.raises(ValueError):
        io.read(f_path)
