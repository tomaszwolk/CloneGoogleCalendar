from app.CloneEventsGoogleCalendar import get_event_details
import pytest

class EventData:
    def __init__(self):
        self.data = {
            }


def event_data_pass_to_function():
    return {
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
            "recurringEventId": '987iofhsd89hvosu8',
            'extendedProperties': {'shared': {'note': 'Event copied from test@gmail.com'}}}


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
            'colorId': '0',
            'extendedProperties': {'shared': {'note': 'Event copied from test@gmail.com'}}}




def test_get_event_details():
    event_data = EventData()
    event = event_data_pass_to_function()
    get_event_details(event, event_data, target_event=None, change_id=False)
    data_to_compare_dict = data_to_compare()
    assert event_data.data == data_to_compare_dict


def event_data_pass_to_function_2():
    return {
            'id': '123456',
            'status': 'confirmed',
            'kind': 'calendar#event',
            'etag': '"3490002330570334"',
            'htmlLink': 'https://www.google.com/calendar/event?eid=XzhncjNnY2hvOGNzamliOWokLmNvbS5wbA',
            'created': '2025-04-17T17:07:57.000Z',
            'updated': '2025-04-18T18:32:45.285Z',
            'summary': 'Priv',
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
            "recurringEventId": '987iofhsd89hvosu8',
            'extendedProperties': {'shared': {'note': 'Event copied from test@gmail.com'}}}

def data_to_compare_2():
    return {
            'id': '123456',
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


def target_event():
    return {
            'id': 'ida08sd0a89sd',
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

def test_get_event_details_2():
    event_data = EventData()
    event = event_data_pass_to_function_2()
    target_event_data = target_event()
    get_event_details(event, event_data, target_event_data, change_id=False)
    data_to_compare_dict = data_to_compare_2()
    assert event_data.data == data_to_compare_dict