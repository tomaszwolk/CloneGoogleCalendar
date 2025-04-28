from app.CloneEventsGoogleCalendar import get_nested_property
import pytest

@pytest.fixture
def data_to_compare():
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
        ("keys, expected"),
        [
            (
                ['extendedProperties', 'shared', 'note'],
                'Event copied from test@gmail.com'
            ),
            (
                ['extendedProperties', 'shared', 'originalID'],
                '_877sa87f5g675656_0d8as'
            ),
        ]
)
def test_get_nested_property(data_to_compare, keys, expected):
    assert get_nested_property(data_to_compare, keys) == expected