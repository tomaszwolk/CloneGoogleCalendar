from app.CloneEventsGoogleCalendar import get_id

CALENDAR_ID = 'test@gmail.com'
TARGET_CALENDAR_ID = 'some_mail@domain.pl'

EVENT_1 = {
    'kind': 'calendar#event',
    'etag': '"3488766735517150"',
    'id': '7khhiebcq22i04sueovmvk6rf4',
    'status': 'confirmed',
    'htmlLink': 'https://www.google.com/calendar/event?eid=N2toaGllYmNxMjJpMDRzdWVvdm12azZyZjQgc2xhd29taXIud29sa0Bib3RsYW5kLmNvbS5wbA',
    'created': '2025-04-11T14:47:05.000Z',
    'updated': '2025-04-11T14:56:07.758Z',
    'summary': 'TEST-Kosz',
    'creator': {'email': 'test@gmail.com', 'self': True},
    'organizer': {'email': 'test@gmail.com', 'self': True},
    'start': {'dateTime': '2025-04-15T17:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'end': {'dateTime': '2025-04-15T17:45:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'iCalUID': '7khhiebcq22i04sueovmvk6rf4@google.com',
    'sequence': 4,
    'reminders': {'useDefault': True},
    'eventType': 'default',
    'attendees': [{'email': 'test@gmail.com', 'organizer': True, 'responseStatus': 'accepted'},
                  {'email': 'some_mail@domain.pl', 'responseStatus': 'accepted'}],
}

EVENT_2 = {
    'kind': 'calendar#event',
    'etag': '"3486823340156606"',
    'id': '6f6cnrcko224327gbu1ihb9tc2_20250425T200000Z', 'status': 'confirmed',
    'htmlLink': 'https://www.google.com/calendar/event?eid=NmY2Y25yY2tvMjI0MzI3Z2J1MWloYjl0YzJfMjAyNTAyMjBUMTAwMDAwWiBzbGF3b21pci53b2xrQGJvdGxhbmQuY29tLnBs',
    'created': '2025-02-06T13:39:24.000Z', 'updated': '2025-03-31T09:01:10.078Z', 'summary': 'Zebranie - Kierownik magazynu',
    'location': 'Gola-Parter-ZOO (6) [TV+Jabra+Camera]', 'creator': {'email': 'mateusz.domagala@botland.com.pl'}, 'organizer': {'email': 'mateusz.domagala@botland.com.pl'},
    'start': {'dateTime': '2025-02-20T11:00:00+01:00', 'timeZone': 'Europe/Warsaw'},
    'end': {'dateTime': '2025-02-20T13:00:00+01:00', 'timeZone': 'Europe/Warsaw'},
    'recurrence': ['RRULE:FREQ=WEEKLY;UNTIL=20250226T225959Z;BYDAY=TH'],
    'iCalUID': '6f6cnrcko224327gbu1ihb9tc2@google.com', 'sequence': 1,
    'attendees':
    [{'email': 'xcx@gmail.com', 'organizer': True, 'responseStatus': 'accepted'},
     {'email': 'zxz@gmail.com',
      'responseStatus': 'accepted'},
     {'email': 'test@gmail.com',
      'self': True, 'responseStatus': 'accepted'},
     {'email': 'c_18832tc9g2iechmehr7goqp9bsali@resource.calendar.google.com', 'displayName': 'Gola-Parter-ZOO (6) [TV+Jabra+Camera]', 'resource': True, 'responseStatus': 'accepted'}],

    'extendedProperties': {'private': {'reclaim.priority.index': '0'}},
    'hangoutLink': 'https://meet.google.com/qwi-snox-cce',
}

EVENT_3 = {
    'kind': 'calendar#event',
    'etag': '"3488766735517150"',
    'id': '_7khhiebcq22_i04sueovmvk6rf4',
    'status': 'confirmed',
    'htmlLink': 'https://www.google.com/calendar/event?eid=N2toaGllYmNxMjJpMDRzdWVvdm12azZyZjQgc2xhd29taXIud29sa0Bib3RsYW5kLmNvbS5wbA',
    'created': '2025-04-11T14:47:05.000Z',
    'updated': '2025-04-11T14:56:07.758Z',
    'summary': 'TEST-Kosz',
    'creator': {'email': 'test@gmail.com', 'self': True},
    'organizer': {'email': 'test@gmail.com', 'self': True},
    'start': {'dateTime': '2025-04-15T17:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'end': {'dateTime': '2025-04-15T17:45:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'iCalUID': '7khhiebcq22i04sueovmvk6rf4@google.com',
    'sequence': 4,
    'reminders': {'useDefault': True},
    'eventType': 'default',
    'attendees': [{'email': 'test@gmail.com', 'organizer': True, 'responseStatus': 'accepted'},
                  {'email': 'some_mail@domain.pl', 'responseStatus': 'accepted'}],
}


def test_get_id_V1():
    assert get_id(EVENT_1['id']) == '7khhiebcq22i04sueovmvk6rf4'


def test_get_id_V2():
    assert get_id(EVENT_2['id']) == '6f6cnrcko224327gbu1ihb9tc2'

def test_get_id_V3():
    assert get_id(EVENT_3['id']) == '7khhiebcq22i04sueovmvk6rf4'


# def test_check_if_event_sequence_is_smaller():
#     assert check_if_event_sequence_is_smaller(
#         EVENT_2, EVENT_1)
#     assert not check_if_event_sequence_is_smaller(
#         EVENT_1, EVENT_2)
