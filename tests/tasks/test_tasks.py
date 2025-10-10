import pkgutil

import tasks.tasks


def test_task_modules_have_required_attributes():
    for _, modname, _ in pkgutil.iter_modules(tasks.tasks.__path__):
        dotted_modname = f"{tasks.tasks.__name__}.{modname}"
        mod = pkgutil.resolve_name(dotted_modname)
        assert hasattr(mod, "main"), (
            f"`{dotted_modname}` does not contain a `main` attribute"
        )
