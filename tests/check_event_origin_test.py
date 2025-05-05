from app.CloneEventsGoogleCalendar import check_event_origin
import pytest

@pytest.fixture
def data():
    return {
    'id': '',
    'status': 'confirmed',
    'summary': '[BTL] Priv',
    'description': '.',
    'organizer': {'email': 'test@gmail.com', 'self': True},
    'start': {'dateTime': '2025-05-08T17:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'end': {'dateTime': '2025-05-08T19:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'reminders': {'useDefault': True},
    'eventType': 'default',
    'colorId': '9',
    'extendedProperties': {'shared': {'note': 'Event copied from test@gmail.com', 'originalID': '_877sa87f5g675656_0d8as'},}}

@pytest.mark.parametrize(
        ("string, expected"),
        [
            ("test@gmail.com", True),
            ("test@domain.pl", False),
        ]
)
def test_check_event_origin(data, string, expected):
    assert check_event_origin(data, string) == expected