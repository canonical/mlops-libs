# Contributing

To make contributions to this repository, you'll need a working [development setup](https://juju.is/docs/sdk/dev-setup).

You can create an environment for development with `tox`:

```shell
tox devenv -e integration
source venv/bin/activate
```

## Library development

This repository is meant for hosting multiple libraries maintained by the MLOps team that can be used by any charm developer.
To contribute, please make sure you are familiar with [libraries](https://juju.is/docs/sdk/library) and follow the standards listed in the [Juju documentation](https://juju.is/docs/sdk/manage-libraries).

## Testing

This project uses `tox` for managing test environments. There are some pre-configured environments
that can be used for linting and formatting code when you're preparing contributions to the charm:

```shell
tox run -e fmt           # update your code according to linting rules
tox run -e lint          # code style
tox run -e unit          # unit tests
tox run -e integration   # integration tests
```

## Deploy

The charm contained in this repository is not meant to be deployed, but for testing purposes only.
