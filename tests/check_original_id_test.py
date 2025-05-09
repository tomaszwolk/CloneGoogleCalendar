from app.CloneEventsGoogleCalendar import check_original_id
import pytest
        
@pytest.mark.parametrize(
        ("event_id, event_data, event_is_a_copy, expected"),
        [
            ('oihj89vsdfd0saf', {}, False, 'oihj89vsdfd0saf'),
            ('oihj89vsdfd0saf', {}, None, 'oihj89vsdfd0saf'),
            ('oihj89vsdfd0saf', {'extendedProperties': {'shared': {'originalID': '_oihj89vsdfd0_saf'}}}, False, '_oihj89vsdfd0_saf'),
            ('oihj89vsdfd0saf', {'extendedProperties': {'shared': {'originalID': '_oihj89vsdfd0_saf'}}}, True, '_oihj89vsdfd0_saf'),
        ]
)
def test_check_original_id(event_id, event_data, event_is_a_copy, expected):
    assert check_original_id(event_id, event_data, event_is_a_copy) == expected