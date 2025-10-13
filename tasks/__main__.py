import argparse
import pkgutil
import sys

import tasks.tasks


TASK_NAMES = {
    x.name for x in pkgutil.iter_modules(tasks.tasks.__path__) if x.name != "__main__"
}


def get_task_module(task_name):
    return pkgutil.resolve_name(f"{tasks.tasks.__name__}.{task_name}")


def main(args):
    arg_dict = parse_args(args)
    match arg_dict["subparser_name"]:
        case "list":
            for task_name in sorted(TASK_NAMES):
                print(task_name)
        case "run":
            get_task_module(arg_dict["task_name"]).main()
        case _:
            raise ValueError


def parse_args(args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="subparser_name")
    subparsers.add_parser("list")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("task_name", choices=TASK_NAMES)
    return vars(parser.parse_args(args))


if __name__ == "__main__":
    main(sys.argv[1:])
