from CloneEventsGoogleCalendar import event_created
import pytest

@pytest.mark.parametrize(
    ("event, email, expected"),
    (
        ({'creator': {'email': 'test@gmail.com'}}, "test@gmail.com", True),
        ({'creator': {'email': 'test2@gmail.com'}}, "test@gmail.com", False),
)
    )
def test_event_created(event, email, expected):
    assert event_created(event, email) == expected