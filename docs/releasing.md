# Releasing

Releases are published to PyPI through GitHub Trusted Publishing. The publisher
must match `.github/workflows/publish.yml` and the GitHub environment `pypi`.
See [PyPI account publishing](https://pypi.org/manage/account/publishing/) for setup.

## Configure the renamed project's publisher

The distribution is `pytest-xspec`. Before the first release under the new
distribution name, create a pending publisher in the intended maintainer's PyPI
account with these values:

| Field | Value |
| --- | --- |
| PyPI project name | `pytest-xspec` |
| GitHub owner | `Thyholt` |
| Repository name | `pytest-xspec` |
| Workflow filename | `publish.yml` |
| Environment name | `pypi` |

Confirm the GitHub repository has the `pypi` environment and the intended release
protection rules. Any publisher configured for the old repository or distribution
must be updated separately. Renaming the repository does not update PyPI publishers.

## Prepare a version

Update the version in [pyproject.toml](../pyproject.toml), then refresh the lockfile:

```sh
uv lock
```

Open a pull request and wait for review and passing CI. Merge it into `master`.
Choose an unused version and tag; repository tags remain shared across distribution
names. The old project's `v0.1.0` and `v0.2.0` tags already exist.

## Publish

Create a GitHub release from `master` with a tag matching the package version,
for example `v0.3.0`. Describe what users can do with this release, then publish it.

Follow the [publishing workflow](../.github/workflows/publish.yml) in GitHub Actions.
After it succeeds, check [the PyPI project](https://pypi.org/project/pytest-xspec/)
and install the released version in a fresh environment.

If a published version has a serious defect, yank it on PyPI and release a fix
with a new version. Published distribution files cannot be replaced.
