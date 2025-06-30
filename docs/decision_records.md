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

[Apache Airflow]: https://airflow.apache.org/
[Dagster]: https://dagster.io/
[Prefect]: https://www.prefect.io/
