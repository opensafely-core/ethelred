# Decision Records

A lightweight alternative to [Architectural Decision Records][].

[Architectural Decision Records]: https://adr.github.io/

## 001: Two applications, one codebase

The `tasks` and `app` modules are, in effect,
separate applications with a shared dependency: the data schema.
To make it easier to make changes to the data schema,
and to avoid setting up and maintaining two codebases,
the applications will live in the same codebase.

## 002: Defer use of orchestration framework

There are several frameworks for orchestrating ETL (Extract, Transform, Load) tasks
(e.g. [Apache Airflow][], [Dagster][], [Prefect][]).
To allow us to focus on gaining insight from the data,
we will defer using (and choosing!) an orchestration framework.

## 003: Continuous integration

> Continuous integration is a software development practice where each member of a team merges their changes into a codebase together with their colleagues' changes at least daily.
>
> [Continuous integration][], Martin Fowler

To reduce the time we spend integrating feature/bugfix branches with the mainline branch,
and to encourage regular pairing and refactoring,
we will adopt continuous integration (CI).

GitHub doesn't make "push to mainline" CI easy
-- checks are run post-merge rather than pre-merge,
which makes it hard to maintain a [healthy mainline branch][1] --
so a GitHub action will automatically open a pull request (PR) for any commits pushed to a non-mainline branch.
We expect this PR to be approved and merged quickly, without comment.

[1]: https://martinfowler.com/articles/branching-patterns.html#healthy-branch
[Apache Airflow]: https://airflow.apache.org/
[Continuous Integration]: https://martinfowler.com/articles/continuousIntegration.html
[Dagster]: https://dagster.io/
[Prefect]: https://www.prefect.io/
