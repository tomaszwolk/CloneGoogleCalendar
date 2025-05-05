from app.CloneEventsGoogleCalendar import check_recurrence
import pytest


@pytest.mark.parametrize(
    ("event, expected"),
    [
        ({'id': '3nosm3b4hohgk3r3q8422ejkgg_20250519T190000Z',
          'recurringEventId': '3nosm3b4hohgk3r3q8422ejkgg'}, True),
        ({'id': 'asdiuv8fd09fs'}, False),
        ({}, False)
    ]
)
def test_check_recurrence(event, expected):
    assert check_recurrence(event) == expected