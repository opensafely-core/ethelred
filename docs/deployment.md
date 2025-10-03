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
It should be set to a DigitalOcean personal access token with the actions:update scope.

For more information about repository secrets,
see the "[Using secrets in GitHub Actions][]" page in the GitHub docs.
For more information about DigitalOcean personal access tokens,
see the "[How to Create a Personal Access Token][]" page in the DigitalOcean docs.

### The app spec

An *app spec* defines an App Platform app's configuration.
It's possible to create, update, and delete an app spec
-- and hence an App Platform app --
from the App Platform Control Panel.
Such changes, however, are not committed to version control.
Consequently, `.do/app.yaml` contains the canonical app spec for the App Platform app.

For more information about app specs,
see the "[How to Update an App's Spec][]" page
and the "[Reference for App Specification][]" page
in the DigitalOcean docs.

### The buildpack

For convenience,
the App Platform app uses a buildpack, rather than a Dockerfile, to build an image.

App Platform uses `requirements.txt` to determine that the Python buildpack is required.
Because the information in this file is already stored elsewhere,
it is a symlink.

For more information about the Python buildpack,
see the "[Python Buildpack on App Platform][]" page in the DigitalOcean docs.

[1]: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#push
[How to Create a Personal Access Token]: https://docs.digitalocean.com/reference/api/create-personal-access-token/
[How to Update an App's Spec]: https://docs.digitalocean.com/products/app-platform/how-to/update-app-spec/
[Python Buildpack on App Platform]: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/python/
[Reference for App Specification]: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
[Using secrets in GitHub Actions]: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
