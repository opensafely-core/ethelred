# Deployment

As [DR001](decision_records.md#001-two-applications-one-codebase) explains,
Ethelred comprises two applications:
the tasks application, within `tasks`;
and the Streamlit app, within `app`.

## The tasks

The tasks application is not deployed.

## The Streamlit app

The Streamlit app is deployed as a DigitalOcean App Platform app using a buildpack.
App Platform uses `requirements.txt` to determine that the Python buildpack is required.
It uses `runtime.txt` to determine which version of Python is required.
Because the information in these files is already stored elsewhere,
they are symlinks.

For more information about the Python buildpack,
see the "[Python Buildpack on App Platform][]" page in the DigitalOcean docs.

[Python Buildpack on App Platform]: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/python/
