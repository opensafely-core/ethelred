# Deployment

As [DR001](decision_records.md#001-two-applications-one-codebase) explains,
Ethelred comprises two applications:
the tasks application, within `tasks`;
and the Streamlit app, within `app`.

## The tasks

The tasks application is not deployed.

## The Streamlit app

The Streamlit app is deployed as a DigitalOcean App Platform app.

### The app spec

An *app spec* defines an App Platform app's configuration.
It's possible to create, update, and delete an app spec
-- and hence an App Platform app --
from the App Platform Control Panel.
Such changes, however, are not committed to version control.
Consequently, `app_spec.yaml` contains the canonical app spec for the App Platform app.

Unfortunately, App Platform doesn't detect changes to `app_spec.yaml`.
To apply the changes, first [install and configure `doctl`][1].
The API token should have the app:update scope, as well as any required scopes.
Then, run:

```sh
just update-app
```

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

[1]: https://docs.digitalocean.com/reference/doctl/how-to/install/
[How to Update an App's Spec]: https://docs.digitalocean.com/products/app-platform/how-to/update-app-spec/
[Python Buildpack on App Platform]: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/python/
[Reference for App Specification]: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
