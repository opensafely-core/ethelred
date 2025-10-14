import abc
import pathlib


class AbstractRepository(abc.ABC): ...


class Repository(AbstractRepository):
    def __init__(self, root_dir):
        root_dir = pathlib.Path(root_dir)
