import pytest

from toolsws.utils import parse_quantity


@pytest.mark.parametrize(
    "value,expected",
    [
        ["0.5", 0.5],
        ["500m", 0.5],
        ["1", 1],
        ["0.5k", 500],
        ["1k", 1000],
        ["1G", 1000000000],
        ["1Gi", 1073741824],
    ],
)
def test_parse_quantity(value, expected):
    assert parse_quantity(value) == expected
