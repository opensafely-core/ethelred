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
Because the information in this file is already stored elsewhere,
it is a symlink.

For more information about the Python buildpack,
see the "[Python Buildpack on App Platform][]" page in the DigitalOcean docs.

[Python Buildpack on App Platform]: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/python/
