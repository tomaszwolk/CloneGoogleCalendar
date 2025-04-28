from app.CloneEventsGoogleCalendar import pop_unnecessary_keys, EventData


class EventData:
    def __init__(self):
        self.data = {
                    'id': '',
                    'status': 'confirmed',
                    'kind': 'calendar#event',
                    'etag': '"3490002330570334"',
                    'htmlLink': 'https://www.google.com/calendar/event?eid=XzhncjNnY2hvOGNzamliOWokLmNvbS5wbA',
                    'created': '2025-04-17T17:07:57.000Z',
                    'updated': '2025-04-18T18:32:45.285Z',
                    'summary': '[BTL] Priv',
                    'description': '.',
                    'creator': {'email': 'test@gmail.com', 'self': True},
                    'organizer': {'email': 'test@gmail.com', 'self': True},
                    'start': {'dateTime': '2025-05-08T17:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
                    'end': {'dateTime': '2025-05-08T19:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
                    'iCalUID': 'D6828C99-3092-42F1-A568-FA1D4C727B34',
                    'sequence': 0,
                    'reminders': {'useDefault': True},
                    'originalStartTime': {'dateTime': '2025-05-08T17:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
                    'eventType': 'default',
                    'colorId': '9',
                    "recurringEventId": '987iofhsd89hvosu8',
                    'extendedProperties': {'shared': {'note': 'Event copied from test@gmail.com'}}
                    }


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
            'extendedProperties': {'shared': {'note': 'Event copied from test@gmail.com'}}}


def test_pop_unnecessary_keys():
    event_data = EventData()
    pop_unnecessary_keys(event_data)
    assert event_data.data == data_to_compare()