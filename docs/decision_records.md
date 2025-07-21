# Decision Records

A lightweight alternative to [Architectural Decision Records][].

## 000: Decisions and their records

We will try to reach decisions by consensus,
recognising that *a* decision is better than *no* decision.
Later decisions my supersede earlier decisions.

We will record our decisions, as they are made, in this document.
We will try not to record our decisions retrospectively.
One decision will correspond to one section;
section headings will follow the observable pattern.
The record should be concise.
It should describe the decision (What?)
and explain the rationale for the decision (Why?).
If a later decision supersedes an earlier decision,
then link to each from the other.

We will link to records as follows:
[DR001](#001-two-applications-one-codebase).

Links and typos aside,
we will treat *records* as immutable.
(We will treat *decisions* as mutable, as later decisions my supersede earlier decisions.)

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

## 004: Treat pull requests as immutable

To facilitate "push to mainline" continuous integration,
a GitHub action will automatically open a pull request (PR) for any commits pushed to a non-mainline branch (see [DR003](#003-continuous-integration)).
These PRs are side-effects of GitHub.
We don't want them to increase the time we spend integrating feature/bugfix branches,
so we will treat them as immutable.

Some process guidance may be helpful:

* If the **checks pass**, approve and merge the PR.
  The branch will be rebased on the mainline branch,
  so either reset your local branch or switch to a new local branch to continue your work.
* If the **checks fail**, close the PR.
  Address the cause of the failure on your local branch and push your commits again.

## 005: Maintain a linear history

> I've always loved the idea of a linear history,
> of rewriting a series until it's perfect
> and getting that nice useful blame and bisecting power.
> Getting rid of that subway map history graph in favor of a nice simple series of patches.
>
> [Fearless rebasing][], Scott Chacon

Continuous integration (see [DR003](#003-continuous-integration)) should make it easier to maintain a linear history,
because there will be fewer opportunities for feature/bugfix branches to diverge from the mainline branch.
Why bother, though?

* It's easier to reason about the output of `git log`.
  There's no need to remember to add `--graph`.
* It's easier to specify a revision correctly.
  There's no need to remember the difference between `~` and `^`.
* If you need to revert, then do you revert the commit?
  The merge commit?
  Both?
  There's no need to ask -- or to answer -- this question.

## 006: Push down or pull up

Pushing down or pulling up computation are [common refactorings][2].
They can also help us decide where computation should take place *before* refactoring is necessary.

An example may help.
Let's say we want to count the number of jobs associated with each job request.
We could produce a table of jobs
and group by job request ID and count job ID.
Producing a table of jobs should probably take place in a task.
What about aggregation?
Aggregation could take place at several levels in the codebase:

* the Streamlit app with Altair (see "[Data Transformations][]")
* the Streamlit app with Pandas (see "[Group by: split-apply-combine][]")
* a task with Pandas
* a task with an SQL query (i.e. the database)

To decide,
we should mentally push down and pull up computation,
considering the implementation effort required at each level.
How much implementation effort is required to address the essential complexity of the problem?
And the accidental complexity?
The *essential complexity* is inherent to the problem.
The *accidental complexity* isn't;
our decisions can increase and decrease the accidental complexity.
Databases were made for aggregation,
so in this case pushing down to a task with an SQL query is reasonable.

[1]: https://martinfowler.com/articles/branching-patterns.html#healthy-branch
[2]: https://refactoring.com/catalog/
[Apache Airflow]: https://airflow.apache.org/
[Architectural Decision Records]: https://adr.github.io/
[Continuous Integration]: https://martinfowler.com/articles/continuousIntegration.html
[Dagster]: https://dagster.io/
[Data Transformations]: https://altair-viz.github.io/user_guide/transform/index.html
[Fearless rebasing]: https://blog.gitbutler.com/fearless-rebasing/
[Group by: split-apply-combine]: https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
[Prefect]: https://www.prefect.io/
