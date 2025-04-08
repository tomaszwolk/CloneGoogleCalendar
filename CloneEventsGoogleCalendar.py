import requests
import json
import uuid
import os
import datetime

from flask import Flask, request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

"""
Calendar Synchronization.
Functions to be performed by the application:
1. automatically generate tokens when they are missing or expired
2. create a webhook with google calendar API
3. retrieve the list of events from the master calendar upon receipt of the webhook
4. checking if the event is all-day or has specific times (start and end)
5. checking the status of the event:
    - adding a new event to the target calendar if it was created by the owner or appeared as a guest
    - if the event is “cancelled” or the invitation was not accepted then remove the event from the target calendar
6 Create a new event in the target calendar, requirements:
    - if the event does not exist in the target calendar
    - copy all and modify summary

Change everywhere 'YOUR_DATA' to your data.
"""

app = Flask(__name__)

# --- Configuration (Replace with your actual values) ---
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
# Replace with your calendar ID in e-mail format (e.g., example@gmail.com).
# Using 'primary' instead of an email address will cause issues when checking the 'responseStatus' of attendees.
CALENDAR_ID = "YOUR_DATA"
# Replace with your calendar ID, string
TARGET_CALENDAR_ID = "YOUR_DATA"
# Your Webhook server URL
WEBHOOK_URL = "YOUR_DATA"
# Channel Id must be unique each time serwer is started
CHANNEL_ID = str(uuid.uuid4())

""" 
--- Visbility ---
"default" - for default value
"private" - if copied event should be private
"public" - event and event details is visible for all readers
None - copy visibility from main calendar
"""
VISIBILITY = "YOUR_DATA"

""" 
--- Enable two-way change of events in calendar. ---
True - if event copies made in target calendar can modifiy events in main calendar - default
False - if event copies made in target calendar can't modifiy events in main calendar
"""
TWO_WAY_CHANGE = "YOUR_DATA"

# For PREFIXES first key in dictionary is default key for main calendar.
# Second key is default for target calendar.
PREFIXES = {
    "[BTL]": "9",
    "[MKS]": "7",
    "[ADSO]": "9",
}

"""
--- OAuth 2.0 Credentials (Replace with your actual credentials) ---
# You will need to set up OAuth 2.0 and obtain these credentials
# This is a simplified example, you should store these securely
# Consider using environment variables or a secrets management service like AWS Secrets Manager, Azure Key Vault, or Google Cloud Secret Manager.
# For example, to use environment variables:
# import os
# TOKEN_PATH = os.getenv('TOKEN_PATH')
# CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH')
# """
TOKEN_PATH = "YOUR_DATA"
TARGET_TOKEN_PATH = "YOUR_DATA"
CREDENTIALS_PATH = "YOUR_DATA"
CREDENTIALS = None
TARGET_CREDENTIALS = None

# --- Load OAuth 2.0 Credentials ---


if os.path.exists(TOKEN_PATH):
    CREDENTIALS = Credentials.from_authorized_user_file(
        TOKEN_PATH, SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not CREDENTIALS or not CREDENTIALS.valid:
    if CREDENTIALS and CREDENTIALS.expired and CREDENTIALS.refresh_token:
        CREDENTIALS.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, SCOPES
        )
        CREDENTIALS = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TOKEN_PATH, "w") as token:
        token.write(CREDENTIALS.to_json())

if os.path.exists(TARGET_TOKEN_PATH):
    TARGET_CREDENTIALS = Credentials.from_authorized_user_file(
        TARGET_TOKEN_PATH, SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not TARGET_CREDENTIALS or not TARGET_CREDENTIALS.valid:
    if TARGET_CREDENTIALS and TARGET_CREDENTIALS.expired and TARGET_CREDENTIALS.refresh_token:
        TARGET_CREDENTIALS.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, SCOPES
        )
        TARGET_CREDENTIALS = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TARGET_TOKEN_PATH, "w") as token:
        token.write(TARGET_CREDENTIALS.to_json())

AUTH_TOKEN = CREDENTIALS.token


class EventData:
    def __init__(self):
        self.data = {
        }


def create_notification_channel(calendar_id: str, webhook_url: str, auth_token: str, channel_id: str):
    """
    Creates a notification channel for a given calendar.

    Args:
        calendar_id (str): The ID of the calendar to create the notification channel for.
        webhook_url (str): The URL to which notifications will be sent.
        auth_token (str): The OAuth 2.0 token for authorization.
        channel_id (str): A unique identifier for the notification channel.

    Optional:
        token (str): A string token that can be used to verify the origin of notifications. 
                     This field is commented out in the payload but can be included if needed.
    """
    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/watch"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "id": channel_id,
        "type": "web_hook",
        "address": webhook_url,
        # "token": "target=myApp-myCalendarChannelDest",  # Optional token
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("Notification channel created successfully!")
        print(response.json())
        return response.json()
    else:
        print("Notification channel HAS NOT BEEN created.")
        print(response.json())
        return response.json()


def validate_post_request() -> str:
    """
    Allow only POST method.
    """
    if request.method == 'POST':
        # print(f"Full headers: {request.headers}")  # Keep for debugging
        resource_state = request.headers.get('X-Goog-Resource-State')
        return resource_state
    else:
        return 405


def time_now_minus_ten_seconds() -> str:
    """
    Checks actual time and subtract from it 10 seconds.
    It's used for getting list of events.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    now_minus_ten_seconds = now - datetime.timedelta(seconds=10)
    now_minus_ten_seconds_iso = now_minus_ten_seconds.isoformat()
    return now_minus_ten_seconds_iso


def get_event_response_status(event: dict) -> str:
    """
    Get invitation response status if there are attendees.
    """
    try:
        attendees = event.get('attendees')
        response_status = ''
        if attendees != None:
            response_status = get_response_status(attendees, CALENDAR_ID)
        return response_status
    except Exception as e:
        print(f"Exception getting response status: {e}")


def get_response_status(attendees: list, email: str = CALENDAR_ID) -> str:
    """Check if the invitation was accepted.

    Args:
        attendees (list): List of event attendees.
        email (str): Email of the main user.

    Possible options:
        - 'needsAction' - invitation not accepted (default) -> create a new event
        - 'declined' - invitation declined -> delete the event (it should have been created when the invitation was received)
        - 'tentative' - the invitation is being considered -> do nothing (event already created)
        - 'accepted' - invitation accepted -> do nothing (event already created)
    """
    for attendee in attendees:
        if attendee['email'] == email:
            return attendee.get('responseStatus')
    return None


def delete_event(calendar_id: str, event_id: str, target_service) -> None:
    """
    Deletes an event from the specified calendar. Checks if already event has been deleted if not appends id to list.

    Args:
        calendar_id (str): The ID of the calendar from which to delete the event.
        event_id (str): The ID of the event to delete.
        target_service (Resource): The Google Calendar API service instance used to interact with the calendar.
    """
    try:
        target_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Event ID: {event_id} deleted")
        return
    except Exception as e:
        print(f"Error deleting event {event_id}: {e}.")
        return None


def check_if_id_exists_in_target_calendar(event_id: str, target_service):
    """
    Extracts the portion of the ID before the first underscore, if present.
    If no underscore is found, returns the original ID.

    Args:
        id (str): The event ID.
        target_service: The Google Calendar API service instance used to interact with the calendar.

    Returns:

    """
    try:
        target_event = target_service.events().get(calendarId=TARGET_CALENDAR_ID,
                                                   eventId=event_id).execute()
        return target_event
    except HttpError:
        return None


def pop_unnecessary_keys(event_data: EventData) -> None:
    """
    Removes keys from the event data that are not required or may cause errors during event creation or update.

    The excluded keys are typically metadata or system-generated fields that are not necessary for creating or updating
    events in the target calendar. For example:
    - "recurringEventId", "originalStartTime": These are related to recurring events and may conflict with new event creation.
    - "kind", "etag", "created", "updated": These are system-generated fields that are not modifiable.
    - "htmlLink", "creator", "organizer", "iCalUID", "sequence": These are informational fields that do not affect event functionality.

    Args:
        event_data (EventData): An instance of the EventData class containing event details.
    """
    data_to_pop = ("recurringEventId", "kind", "created", "updated", "etag",
                   "originalStartTime", "htmlLink", "creator", "organizer", "iCalUID", "sequence")
    try:
        event_data.data = {
            key: value for key, value in event_data.data.items() if key not in data_to_pop}
    except Exception as e:
        print(f"Exception pop_unnecessary_keys: {e}")


def get_event_details(event: dict, event_data: dict, target_event: dict):
    """
    Retrieves details of a specific event and updates instance of class EventData.data.

    Args:
        event (dict): The event data from Google Calendar.
        event_data (EventData): An instance of EventData to store the event details.
        target_event (dict): The event data from the target calendar, used to compare and update details.
        change_id (bool): A flag indicating whether to modify the event ID to remove recurrence-specific timestamps.
    """
    try:
        """
        Get iCalUID instead of id, because id for recurrence get "id_timestamp"
        which is different for all-day event and for not all-day event.
        Beginning of id and iCalUID is the same. iCalUID has at the end @google.com so it has to be removed.
        Uncomment # data if you want to manualy change them."""
        event_data.data = event

        summary = event.get('summary')
        summary_prefix_len = summary.find("]") + 1

        # Check if event exist in target calendar.
        # If yes then check if summary prefix is:
        # - the same in main and target calendar then copy summary:
        #   - colorId = 0 if prefix is same as default in target calendar
        #   - colorId = from PREFIXES if prefix is not same as default in target calendar
        # - the same as default in target calendar but target calendar doesn't have prefix then copy summary without prefix and colorId = 0 (this means in target calendar is original event without prefix)
        # - not in the PREFIXES then add default prefix and colorId = default
        # else event doesn't exists -> add default prefix is it's not been added already

        color_id = "0"
        if target_event:
            target_event_summary = target_event.get('summary')
            if summary_prefix_len == 0:
                first_key = next(iter(PREFIXES))
                summary = first_key + " " + summary
                color_id = PREFIXES[first_key]
            elif summary[:summary_prefix_len] == target_event_summary[:summary_prefix_len] == list(PREFIXES)[1]:
                summary = summary
                color_id = "0"
            elif summary[:summary_prefix_len] == target_event_summary[:summary_prefix_len]:
                summary = summary
                color_id = PREFIXES[summary[:summary_prefix_len]]
            elif summary[:summary_prefix_len] == list(PREFIXES)[1]:
                summary = summary[summary_prefix_len + 1:]
                color_id = "0"
            else:
                first_key = next(iter(PREFIXES))
                summary = first_key + " " + summary
                color_id = PREFIXES[first_key]
        else:
            first_key = next(iter(PREFIXES))
            if summary[:summary_prefix_len] == first_key:
                summary = summary
            else:
                summary = first_key + " " + summary
            color_id = PREFIXES[first_key]

        event_data.data.update({"summary": summary})
        event_data.data.update({"colorId": color_id})

        if VISIBILITY is not None or not "YOUR_DATA":
            event_data.data.update({"visibility": VISIBILITY})

        pop_unnecessary_keys(event_data)

        return
    except Exception as e:
        print(
            f"Error getting event details for event {event.get('id')}: {e}. Event details: {event}")
        return None


def add_extended_properties(event_data: EventData) -> None:
    extended_properties = {
        'shared': {
            'note': f'Event copied from {CALENDAR_ID}'
        }
    }
    event_data.data.update(
        {"extendedProperties": extended_properties})


def create_new_event(calendar_id: str, event_data: EventData, service) -> None:
    """
    Creates a new event in the specified calendar.

    Args:
        - calendar_id: The ID of the calendar to create the event in (CALENDAR_ID_TO_ADD).
        - event_data: An instance of EventData
        - service: The Google Calendar API service instance used to interact with the calendar.
    """
    # if event_data.data.get('id') in event_list_id:
    #     print("Not creating event. Event already exists in target calendar.")
    #     return
    add_extended_properties(event_data)
    try:
        event = service.events().insert(calendarId=calendar_id,
                                        body=event_data.data, conferenceDataVersion=1, supportsAttachments=True).execute()
        print(
            f"Event created: {event.get('htmlLink')}\n{event_data.data}\n")
    except Exception as e:
        print(f"Error creating event: {e}")


def update_event(target_service, event_data: EventData, target_event: dict) -> None:
    """
    Updates event in target calendar.

    Args:
    - target_service: The Google Calendar API service instance used to interact with the calendar.
    - event_data: An instance of EventData containing the event details to update.
    - target_event: A dictionary representing the event data from the target calendar. 
    """
    target_event_id = target_event.get('id')
    try:
        target_service.events().update(calendarId=TARGET_CALENDAR_ID,
                                       eventId=target_event_id, body=event_data.data, conferenceDataVersion=1, supportsAttachments=True).execute()
        print(
            f"Event: {event_data.data.get('summary', 'No summary')}, ID: {target_event_id} has been updated.")
    except Exception as e:
        print(
            f"Error updating event {event_data.data.get('summary', 'No summary')}, {target_event_id}: {e}")
        return


@app.route('/notifications', methods=['POST'])
def notifications():
    """
    Handles incoming notification messages from the Google Calendar API.
    """
    resource_state = validate_post_request()
    if resource_state == 405:
        print("405 - Method Not Allowed")
        return "Method Not Allowed", 405
    # *** Handle sync messages ***
    if resource_state == 'sync':
        print("This is a sync message.")
        return "OK", 200
    elif resource_state == 'exists':
        service = build("calendar", "v3",
                        credentials=CREDENTIALS, cache_discovery=False)
        target_service = build("calendar", "v3",
                               credentials=TARGET_CREDENTIALS, cache_discovery=False)
        try:
            page_token = None
            while True:
                # Retrieve the list of events from the master calendar that has been changed in last 10 seconds
                now_minus_ten_seconds_iso = time_now_minus_ten_seconds()
                events_result = service.events().list(calendarId=CALENDAR_ID,
                                                      updatedMin=now_minus_ten_seconds_iso,
                                                      singleEvents=False, maxResults=250, pageToken=page_token).execute()
                events = events_result.get('items', [])
                if events:
                    for event in events:
                        extended_properties = event.get(
                            'extendedProperties', {}).get('shared', {}).get('note', "")
                        if TWO_WAY_CHANGE == False and extended_properties[:17] == "Event copied from":
                            print("Event copied from main calendar. Skip.")
                            continue
                        event_type = event.get('eventType')
                        if event_type == 'workingLocation' or event_type == 'birthday':
                            print("Event type: working location or birthday. Skip.")
                            continue
                        # Check if event exists in target calendar - needed to know if it should be updated or created.
                        # Also if event exists, then check summary prefixes - used in get_event_details function.
                        event_id = event.get('id')
                        target_event = check_if_id_exists_in_target_calendar(
                            event_id, target_service)
                        event_data = EventData()
                        status = event.get('status')
                        response_status = get_event_response_status(event)
                        if target_event == None and status != 'cancelled' and response_status != 'declined':
                            get_event_details(
                                event, event_data, target_event)
                            create_new_event(TARGET_CALENDAR_ID,
                                             event_data, target_service)
                            continue
                        if status == 'cancelled' or response_status == 'declined':
                            print(
                                f"Status: {status}. Response status: {response_status}")
                            delete_event(TARGET_CALENDAR_ID,
                                         event_id, target_service)
                            continue
                        else:
                            get_event_details(
                                event, event_data, target_event)
                            update_event(target_service,
                                         event_data, target_event)
                            continue
                page_token = events_result.get('nextPageToken')
                if not page_token:
                    break
        except Exception as e:
            print(f"Error listing events: {e}")
    return "OK", 200


# --- Run the channel creation when the app starts ---
with app.app_context():
    create_notification_channel(
        CALENDAR_ID, WEBHOOK_URL, AUTH_TOKEN, CHANNEL_ID)

# --- Run the Flask app ---
if __name__ == '__main__':
    app.run()
