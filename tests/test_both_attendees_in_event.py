import pytest
from CloneEventsGoogleCalendar import check_if_both_calendars_in_attendees

# test_CloneEventsGoogleCalendar.py
# Mock constants
CALENDAR_ID = "test@gmail.com"
TARGET_CALENDAR_ID = "target@gmail.com"


@pytest.mark.parametrize(
    "event, expected",
    [
        # Case 1: Both CALENDAR_ID and TARGET_CALENDAR_ID are present
        ({"attendees": [{"email": "test@gmail.com"},
                        {"email": "target@gmail.com"}]}, True),
        # Case 2: Only CALENDAR_ID is present
        ({"attendees": [{"email": "test@gmail.com"}]}, False),
        # Case 3: Only TARGET_CALENDAR_ID is present
        ({"attendees": [{"email": "target@gmail.com"}]}, False),
        # Case 4: Neither CALENDAR_ID nor TARGET_CALENDAR_ID is present
        ({"attendees": [{"email": "other@gmail.com"}]}, False),
        # Case 5: Empty attendees list
        ({"attendees": []}, False),
        # Case 6: No attendees key in the event
        ({}, False),
    ],
)
def test_check_if_both_calendars_in_attendees(monkeypatch, event, expected):
    # Mock constants in module
    monkeypatch.setattr("CloneEventsGoogleCalendar.CALENDAR_ID", CALENDAR_ID)
    monkeypatch.setattr(
        "CloneEventsGoogleCalendar.TARGET_CALENDAR_ID", TARGET_CALENDAR_ID)
    assert check_if_both_calendars_in_attendees(event) == expected
