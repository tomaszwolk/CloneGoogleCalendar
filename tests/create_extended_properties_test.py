from app.CloneEventsGoogleCalendar import create_extended_properties
import pytest
from datetime import datetime

CALENDAR_ID = 'test@gmail.com'
TARGET_CALENDAR_ID = 'test@domain.pl'

@pytest.mark.parametrize(
        ("event_id, time_now, event_is_a_copy, expected"),
        [
            ('oiu897b78n', datetime(2025, 4, 1, 21, 37), False, 
            {
                'shared': {
                'note': f'Event copied from {CALENDAR_ID}',
                'timestamp': '2025-04-01T21:37:00',
                'originalID': 'oiu897b78n'
                }
            }),
            ('oiu897b78n', datetime(2025, 4, 1, 21, 37), True, 
            {
                'shared': {
                'note': f'Event copied from {TARGET_CALENDAR_ID}',
                'timestamp': '2025-04-01T21:37:00',
                'originalID': 'oiu897b78n'
                }
            }),
        ]
)
def test_create_extended_properties(monkeypatch, event_id, time_now, event_is_a_copy, expected):
    # Mock constants in module
    monkeypatch.setattr("app.CloneEventsGoogleCalendar.CALENDAR_ID", CALENDAR_ID)
    monkeypatch.setattr(
        "app.CloneEventsGoogleCalendar.TARGET_CALENDAR_ID", TARGET_CALENDAR_ID)
    assert create_extended_properties(event_id, time_now, event_is_a_copy) == expected