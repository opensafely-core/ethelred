# Deployment

As [DR001](decision_records.md#001-two-applications-one-codebase) explains,
Ethelred comprises two applications:
the tasks application, within `tasks`;
and the Streamlit app, within `app`.

## The tasks

The tasks application is not deployed.

## The Streamlit app

The Streamlit app is deployed as a DigitalOcean App Platform app.

### The GitHub Actions workflows

The Continuous Deployment workflow (`.github/workflows/cd.yaml`) deploys the Streamlit app on [a push event][1] to the mainline branch
(a push event corresponds to a push, merge, or rebase).
It does so only after all jobs in the Continuous Integration workflow (`.github/workflows/ci.yaml`) succeeded (or were skipped).

The Continuous Deployment workflow requires a repository secret called `DIGITALOCEAN_DEPLOYMENT`.
It should be set to a DigitalOcean personal access token with the app:update scope.

For more information about repository secrets,
see the "[Using secrets in GitHub Actions][]" page in the GitHub docs.
For more information about DigitalOcean personal access tokens,
see the "[How to Create a Personal Access Token][]" page in the DigitalOcean docs.

### The app spec

An *app spec* defines an App Platform app's configuration.
Every app has an app spec.
Indeed, changes to an app's configuration made through the App Platform Control Panel are,
in effect, changes to the app's app spec.
It's important to realise that *each change redeploys the app*;
the new deployment has a different app spec to the old deployment.

Whilst it's possible to commit an app spec,
the committed app spec isn't used when the app is redeployed.
Instead, the new deployment uses the same app spec as the old deployment,
plus or minus the change that triggered the redeployment.
In this way, the committed app spec and the applied app spec may drift.

Ethelred's app spec is committed to `.do/app.yaml`.[^1]
Ensuring that the committed app spec is used instead of the applied app spec
is the responsibility of the Continuous Deployment workflow.

For more information about app specs,
see the "[How to Update an App's Spec][]" page
and the "[Reference for App Specification][]" page
in the DigitalOcean docs.

#### Environment variables

We could set an environment variable through the App Platform Control Panel.
Doing so would redeploy the app;
the environment variable would then be available in the new deployment.
However, the next time the Continuous Deployment workflow succeeded,
the committed app spec would be used instead of the applied app spec,
and the environment variable would no longer be available in the new deployment.
What to do?

In some cases,
it's sufficient to hard-code the value of the environment variable in the app spec.
For example, in `.do/app.yaml`:

```yaml
envs:
  - key: STREAMLIT_SERVER_PORT
    value: "8080"
```

In other cases,
the value of the environment variable should reference *another* environment variable,
using [bash-style parameter expansion][2].
For example, in `.do/app.yaml`:

```yaml
envs:
  - key: REPOSITORY_ROOT_URI
    value: ${REPOSITORY_ROOT_URI}
```

The other environment variable should be available in the environment created for the Continuous Deployment workflow's `deploy` job.
The value of the other environment variable should reference a GitHub Actions [variable][3] or [context][4],
using GitHub Actions-style parameter expansion.
For example, in `.github/workflows/cd.yaml`:

```yaml
env:
  REPOSITORY_ROOT_URI: ${{ vars.REPOSITORY_ROOT_URI }}
```

Notice that we could have three different names for the same variable.
Let's not!

### The buildpack

For convenience,
the App Platform app uses a buildpack, rather than a Dockerfile, to build an image.

App Platform's Python buildpack supports `uv`, our package manager.
Other package manager files (such as `requirements.txt`) must not be present in the
repo for the buildpack to use `uv`.

For more information about the Python buildpack,
see the "[Python Buildpack on App Platform][]" page in the DigitalOcean docs.

[1]: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#push
[2]: https://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html
[3]: https://docs.github.com/en/actions/reference/workflows-and-actions/variables
[4]: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts
[digitalocean/app_action]: https://github.com/digitalocean/app_action
[How to Create a Personal Access Token]: https://docs.digitalocean.com/reference/api/create-personal-access-token/
[How to Update an App's Spec]: https://docs.digitalocean.com/products/app-platform/how-to/update-app-spec/
[Python Buildpack on App Platform]: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/python/
[Reference for App Specification]: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
[Using secrets in GitHub Actions]: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets

[^1]:
    This is the default for the [digitalocean/app_action][]/deploy workflow,
    which is used by the Continuous Deployment workflow.
