from app.CloneEventsGoogleCalendar import check_timestamp
import pytest
from datetime import datetime


@pytest.mark.parametrize(
        ("event, time_now, expected"),
        [
            ({'extendedProperties': 
              {'shared': 
               {'note': 'Event copied from test@gmail.com', 'originalID': '_877sa87f5g675656_0d8as', 'timestamp': '2025-04-01T21:37:00'},}},
            datetime(2025, 4, 1, 21, 37, 5),
            False
            ),
            ({'extendedProperties': 
              {'shared': 
               {'note': 'Event copied from test@gmail.com', 'originalID': '_877sa87f5g675656_0d8as', 'timestamp': '2025-04-01T21:37:00'},}},
            datetime(2025, 4, 1, 21, 37, 10),
            False
            ),
            ({'extendedProperties': 
              {'shared': 
               {'note': 'Event copied from test@gmail.com', 'originalID': '_877sa87f5g675656_0d8as', 'timestamp': '2025-04-01T21:37:00'},}},
            datetime(2025, 4, 1, 21, 37, 10, 1),
            True
            ),
            ({'extendedProperties': 
              {'shared': 
               {'note': 'Event copied from test@gmail.com', 'originalID': '_877sa87f5g675656_0d8as'},}},
            datetime(2025, 4, 1, 21, 37, 10, 1),
            None
            ),
        ]
)
def test_check_timestamp(event, time_now, expected):
    assert check_timestamp(event, time_now) == expected