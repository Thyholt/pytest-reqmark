import pytest


@pytest.mark.req("REQ-001")
def test_cat_has_a_name():
    cat = {"name": "Chairman Meow"}

    name = cat["name"]

    assert name == "Chairman Meow"


@pytest.mark.req("REQ-001")
@pytest.mark.skip(reason="The cat declined the meeting invitation.")
def test_cat_attends_meetings():
    attendees = ["Chairman Meow"]

    cat_is_present = "Chairman Meow" in attendees

    assert cat_is_present
