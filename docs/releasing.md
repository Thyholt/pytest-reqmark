# Releasing

Releases are published to PyPI through GitHub Trusted Publishing. The publisher
must match `.github/workflows/publish.yml` and the GitHub environment `pypi`.
See [PyPI account publishing](https://pypi.org/manage/account/publishing/) for setup.

## Prepare a version

Update the version in [pyproject.toml](../pyproject.toml), then refresh the lockfile:

```sh
uv lock
```

Open a pull request and wait for review and passing CI. Merge it into `master`.
The first release uses the existing version `0.1.0`.

## Publish

Create a GitHub release from `master` with a tag matching the package version,
for example `v0.1.0`. Describe what users can do with this release, then publish it.

Follow the [publishing workflow](../.github/workflows/publish.yml) in GitHub Actions.
After it succeeds, check [the PyPI project](https://pypi.org/project/pytest-reqmark/)
and install the released version in a fresh environment.

If a published version has a serious defect, yank it on PyPI and release a fix
with a new version. Published distribution files cannot be replaced.
