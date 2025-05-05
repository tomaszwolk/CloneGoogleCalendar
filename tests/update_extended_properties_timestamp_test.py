from app.CloneEventsGoogleCalendar import update_extended_properties_timestamp, EventData
from datetime import datetime
import pytest


@pytest.mark.parametrize(
        ("time_now, expected"),
        [
            (datetime(2025, 4, 1, 21, 37), 
             {'extendedProperties':
              {'shared': {'timestamp': '2025-04-01T21:37:00'}}}),
        ]
)
def test_update_extended_properties_timestamp(time_now, expected):
    event_data = EventData()
    update_extended_properties_timestamp(event_data, time_now) 
    assert event_data.data == expected