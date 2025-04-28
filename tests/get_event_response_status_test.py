from app.CloneEventsGoogleCalendar import get_event_response_status
import pytest


@pytest.mark.parametrize(
        ("event, email, expected"),
        [
            ({'attendees': 
                [{'email': 'me@you.pl', 'organizer': True, 'responseStatus': 'accepted'}, 
                {'email': 'someone@domain.com', 'responseStatus': 'accepted'}, 
                {'email': 'test@gmail.com', 'self': True, 'responseStatus': 'accepted'}, 
                {'email': 'c_18832tc9g2iechoiehr7goqp9bsali@resource.calendar.google.com', 'displayName': 'Biuro (6) [TV+Jabra+Camera]', 'resource': True, 'responseStatus': 'accepted'}],},
            'test@gmail.com',
            'accepted'),
            ({'attendees': 
                [{'email': 'me@you.pl', 'organizer': True, 'responseStatus': 'accepted'},
                {'email': 'test@gmail.com', 'self': True, 'responseStatus': 'needsAction'}],}, 
            'test@gmail.com',
            'needsAction'),
            ({'attendees': 
                [{'email': 'me@you.pl', 'organizer': True, 'responseStatus': 'accepted'}],}, 
            'test@gmail.com',
            ''),
            ({}, 
            'test@gmail.com',
            ''),
        ]
)
def test_get_event_response_status(event, email, expected):
    assert get_event_response_status(event, email) == expected


