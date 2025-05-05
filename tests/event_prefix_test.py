from app.CloneEventsGoogleCalendar import event_prefix
import pytest

@pytest.mark.parametrize(
        ("summary, expected"),
        [
            ("[BTL] Something", "[BTL]"),
            ("Another something", None),
            ("[xxx] YYY", None),
            ("[adso] Testowe", "[ADSO]")
        ]
)
def test_event_prefix(summary, expected):
    assert event_prefix(summary) == expected