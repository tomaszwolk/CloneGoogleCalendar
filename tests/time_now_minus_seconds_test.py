from app.CloneEventsGoogleCalendar import time_now_minus_seconds, time_now_minus_seconds_iso
import pytest
import datetime


@pytest.mark.parametrize(
        ("time_now, seconds, expected"),
        [
            (datetime.datetime(2025, 4, 1, 8, 29, 15),
             10,
             datetime.datetime(2025, 4, 1, 8, 29, 5)),
            (datetime.datetime(2025, 4, 1, 8, 29, 00),
             10,
             datetime.datetime(2025, 4, 1, 8, 28, 50)),
        ]
)
def test_time_now_minus_seconds(time_now, seconds, expected):
    assert time_now_minus_seconds(time_now, seconds) == expected


@pytest.mark.parametrize(
        ("time_now, expected"),
        [
            (datetime.datetime(2025, 4, 1, 8, 29, 15),
             datetime.datetime(2025, 4, 1, 8, 29, 5)),            
        ]
)
def test_time_now_minus_seconds2(time_now, expected):
    assert time_now_minus_seconds(time_now) == expected


@pytest.mark.parametrize(
        ("time_now, seconds, expected"),
        [
            (datetime.datetime(2025, 4, 1, 8, 29, 15), 10, "2025-04-01T08:29:05")
        ]
)
def test_time_now_minus_seconds_iso(time_now, seconds, expected):
    assert time_now_minus_seconds_iso(time_now, seconds) == expected