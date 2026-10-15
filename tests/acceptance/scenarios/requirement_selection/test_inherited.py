import pytest

pytestmark = pytest.mark.xspec("REQ-003")


def test_module_behavior() -> None:
    print("TEST BODY EXECUTED: test_inherited.py::test_module_behavior")


@pytest.mark.xspec("REQ-004")
class TestBehavior:
    @pytest.mark.parametrize("value", ["first", "second"])
    def test_parameterized_behavior(self, value: str) -> None:
        assert value in ("first", "second")
        print(
            "TEST BODY EXECUTED: "
            f"test_inherited.py::TestBehavior::test_parameterized_behavior[{value}]"
        )
