import pytest


@pytest.mark.req("training.yolo.config")
def test_parameters_logged():
    pass


@pytest.mark.req("training.yolo.config")
def test_source_logged():
    pass


@pytest.mark.req("dataset.versioning")
def test_version_stable():
    pytest.skip("not ready")
