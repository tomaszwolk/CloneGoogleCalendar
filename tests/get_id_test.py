import pytest
from app.CloneEventsGoogleCalendar import get_id

@pytest.mark.parametrize(
    "id, expected",
    [
        ("6f6cnrcko224327gbu1ihb9tc2_20250425T200000Z", "6f6cnrcko224327gbu1ihb9tc2"),
        ("6f6cnrcko224327gbu1ihb9tc2_20250425", "6f6cnrcko224327gbu1ihb9tc2"),
        ("_6f6cnrcko224327gbu1ihb9tc2", "6f6cnrcko224327gbu1ihb9tc2"),
        ("_kjh89987hnv_sa098djcj", "kjh89987hnvsa098djcj")
    ]
)
def test_get_id(id, expected):
    assert get_id(id) == expected
