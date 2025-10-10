import hashlib

from . import io


def get_repo(url):
    return url.split("/")[-1]


def load_project_definition(project_definitions_dir, repo, sha):
    return io.read(project_definitions_dir / repo / f"{sha}.pickle")


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
