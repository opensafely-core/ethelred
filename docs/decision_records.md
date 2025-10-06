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

## 007: Contain Pandas

Not pandas, but [Pandas][]: The Python Data Analysis Library.
Wes McKinney,
creator and BDFL of Pandas,
recognises several shortcomings in "[Apache Arrow and the '10 things I hate about Pandas'][3]".
He describes group by operations as "awkward",
but it's not just group by operations;
*many* operations are awkward.
What does `.loc` return?
And `.iloc`?
Why is it possible to index into a `DatetimeIndex` with a string,
but not a `datetime.date`?
Why does "[Reshaping and pivot tables][]" use different words to describe the same concepts?

It's unfortunate that Pandas' `DataFrame` has become the *de facto* tabular data structure.
It's even more unfortunate that it's hard to work with Streamlit and Altair without it.
For these reasons, we can't remove Pandas.
However, we can contain it.

A repository is a good place to contain Pandas (`app.repositories.Repository`).
Not only can a repository's methods be tested in isolation,
but a repository can be faked when necessary.
And, when we decide to replace Ethelred's data store,
then we need only modify a repository's methods.
If we find ourselves writing `import pandas` anywhere other than in `app/repositories.py`,
then we should either push down or pull up ([DR006](#006-push-down-or-pull-up)).

## 008: Use CSV files as the interface

We will use CSV files as the interface between the two applications that comprise Ethelred ([DR001](#001-two-applications-one-codebase)).
CSV files are quick to write (by `tasks`) and read (by `app`),
and unlike tables in an RDBMS,
require no up-front definition.

## 009: Source directories and `PYTHONPATH`

Although Streamlit apps are Python modules,
to support reruns,
they aren't imported using [the standard import system][4] (i.e. the `import` statement).

> Reruns are a central part of every Streamlit app.
> When users interact with widgets,
> your script reruns from top to bottom,
> and your app's frontend is updated.
>
> [Working with fragments][]

Not using the standard import system means we need to add some configuration to ensure:

* modules are imported correctly when the Streamlit app is run *and* when the test suite is run;
* imports are ordered according to [the accepted conventions][5];
* and most importantly, nobody is confused.

More specifically,
we set `tool.ruff.src` in `pyproject.toml`
and `PYTHONPATH` when invoking Coverage.py with `just test`.

## 010: GitHub flow

With [003](#003-continuous-integration) and [004](#004-treat-pull-requests-as-immutable),
we adopted continuous integration (CI).
Whilst we experienced several advantages of CI,
we also experienced several disadvantages.
Specifically, we felt there wasn't a suitable means of reviewing a set of changes,
especially when pairing wasn't feasible.

For this reason,
we will adopt [GitHub flow][] *alongside* CI.

Some process guidance may be helpful.
For both GitHub flow and CI:

* create a local branch
* make changes
* commit and push
* a GitHub action will automatically open a pull request (PR)

For GitHub flow:
* edit the PR's title and description
* request a review
* address review comments
* approve and merge the PR

For CI:
* If the checks pass, approve and merge the PR.
* If the checks fail, close the PR.

## 011: Deploying the Streamlit app

We will deploy the Streamlit app as a DigitalOcean [App Platform][] app.
We had a positive experience of App Platform when we deployed OpenPrescribing Hospitals.
We considered using [Dokku][6],
but have found Dokku hard to reason about.

## 012: Use a buildpack rather than a Dockerfile

With [011](#011-deploying-the-streamlit-app), we deployed the Streamlit app as an App Platform app.
There are two mechanisms for building images for App Platform apps:
either buildpacks or Dockerfiles.
For convenience, we will use a buildpack.
To make it easier to reason about the image, however, we will eventually use a Dockerfile.

## 013: Adopt Ship / Show / Ask

With [010](#010-github-flow),
we adopted GitHub flow alongside continuous integration (CI).
Having done so,
we realised the branching strategy we were aiming for was already documented:
it's called [Ship / Show / Ask][].

* **Ship** corresponds to "push to mainline" CI
  ([003](#003-continuous-integration) and [004](#004-treat-pull-requests-as-immutable)).
* **Show** corresponds to GitHub flow with a post-merge review
  ([010](#010-github-flow)).
* **Ask** corresponds to GitHub flow with a pre-merge review
  ([010](#010-github-flow)).

We will adopt Ship / Show / Ask.
Doing so necessitates the following changes:

* To allow us to ship,
  we will remove branch protection rules from the mainline branch.
* To allow us to show,
  we will allow PRs to be integrated into the mainline branch without approval.
* To allow us to ask,
  we will remove the GitHub action that automatically opens a pull request (PR) for any commits pushed to a non-mainline branch.

It's important to emphasise that we will continue to maintain a [healthy mainline branch][1]
by running checks on each push event
(a push event corresponds to a push, merge, or rebase).

[1]: https://martinfowler.com/articles/branching-patterns.html#healthy-branch
[2]: https://refactoring.com/catalog/
[3]: https://wesmckinney.com/blog/apache-arrow-pandas-internals/
[4]: https://docs.python.org/3.12/reference/import.html
[5]: https://docs.astral.sh/ruff/settings/#lint_isort_section-order
[6]: https://bennett.wiki/tools-systems/dokku/
[Apache Airflow]: https://airflow.apache.org/
[App Platform]: https://docs.digitalocean.com/products/app-platform/
[Architectural Decision Records]: https://adr.github.io/
[Continuous Integration]: https://martinfowler.com/articles/continuousIntegration.html
[Dagster]: https://dagster.io/
[Data Transformations]: https://altair-viz.github.io/user_guide/transform/index.html
[Fearless rebasing]: https://blog.gitbutler.com/fearless-rebasing/
[GitHub Flow]: https://docs.github.com/en/get-started/using-github/github-flow
[Group by: split-apply-combine]: https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
[Pandas]: https://pandas.pydata.org/
[Prefect]: https://www.prefect.io/
[Reshaping and pivot tables]: https://pandas.pydata.org/pandas-docs/stable/user_guide/reshaping.html
[Ship / Show / Ask]: https://martinfowler.com/articles/ship-show-ask.html
[Working with fragments]: https://docs.streamlit.io/develop/concepts/architecture/fragments
