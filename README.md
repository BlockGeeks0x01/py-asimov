# py-asimov

![PyPI - License](https://img.shields.io/pypi/l/py-asimov?color=1&style=plastic)
![PyPI](https://img.shields.io/pypi/v/py-asimov?style=plastic)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/py-asimov?style=plastic)
[![Documentation Status](https://readthedocs.org/projects/py-asimov/badge/?version=latest)](https://py-asimov.readthedocs.io/en/latest/?badge=latest)

## Quickstart

```sh
pip install py-asimov
```

## API
[pyasimov api](./api.md)

## Tutorial
[Tutorial](./tutorial.md)

## Developer Setup

If you would like to hack on py-asimov, please follow these steps:

- Testing
- Pull Requests
- Code Style
- Documentation

### Development Environment Setup

You can set up your dev environment with:

```sh
git clone git@gitlab.asimov.work:asimov/asimov-python-sdk.git
cd pyasimov
pyenv virtualenv 3.7.3 env-asimov
pyenv activate env-asimov
pip install -e .[dev]
 
# If you're using zsh you need to escape square brackets: 
pip install -e .\[extra\]
```

### Testing Setup

During development, you might like to have tests run on every file save.

```sh
# in the project root:
make test
```

### Release setup

For Debian-like systems:
```
apt install pandoc
```

To release a new version:

```sh
make release bump=$$VERSION_PART_TO_BUMP$$
```

#### How to bumpversion

The version format for this repo is `{major}.{minor}.{patch}` for stable, and
`{major}.{minor}.{patch}-{stage}.{devnum}` for unstable (`stage` can be alpha or beta).

To issue the next version in line, specify which part to bump,
like `make release bump=minor` or `make release bump=devnum`. This is typically done from the
master branch, except when releasing a beta (in which case the beta is released from master,
and the previous stable branch is released from said branch). To include changes made with each
release, update "docs/releases.rst" with the changes, and apply commit directly to master 
before release.

If you are in a beta version, `make release bump=stage` will switch to a stable.

To issue an unstable version when the current version is stable, specify the
new version explicitly, like `make release bump="--new-version 4.0.0-alpha.1 devnum"`
