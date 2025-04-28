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
3. retrieve the list of events from master calendar upon receipt of the webhook
4. checking if the event is all-day or has specific times (start and end)
5. checking the status of the event:
    - adding a new event to the target calendar if it was created by the owner
        or appeared as a guest
    - if the event is “cancelled” or the invitation was not accepted then
        remove the event from the target calendar
6 Create a new event in the target calendar, requirements:
    - if the event does not exist in the target calendar
    - copy all and modify summary

Change everywhere 'YOUR_DATA' to your data.
"""

app = Flask(__name__)

# --- Configuration (Replace with your actual values in file config.ini) ---
SCOPES = "YOUR_DATA"
CALENDAR_ID = "YOUR_DATA"
TARGET_CALENDAR_ID = "YOUR_DATA"
WEBHOOK_URL = "YOUR_DATA"
CHANNEL_ID = str(uuid.uuid4())
VISIBILITY = "YOUR_DATA"
TWO_WAY_CHANGE = "YOUR_DATA"
PREFIXES = {
    "[BTL]": "9",
    "[MKS]": "7",
    "[ADSO]": "9",
}


"""
--- OAuth 2.0 Credentials (Replace with your actual credentials) ---
# You will need to set up OAuth 2.0 and obtain these credentials
# This is a simplified example, you should store these securely
# Consider using environment variables or a secrets management service like 
# AWS Secrets Manager, Azure Key Vault, or Google Cloud Secret Manager.
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
AUTH_TOKEN = None

timezone = datetime.timezone(datetime.timedelta(
    hours=0))  # Choose your serwer timezone
Last_update_timestamp = datetime.datetime(2025, 4, 1, 8, 0, tzinfo=timezone)


class EventData:
    def __init__(self):
        self.data = {
        }


def create_token():
    """
    Creates a token for the Google Calendar API.
    """
    global CREDENTIALS, TARGET_CREDENTIALS, AUTH_TOKEN
    global TOKEN_PATH, TARGET_TOKEN_PATH, CREDENTIALS_PATH, SCOPES
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


def create_notification_channel(calendar_id: str,
                                webhook_url: str,
                                auth_token: str,
                                channel_id: str):
    """
    Creates a notification channel for a given calendar.

    Args:
        calendar_id (str): The ID of the calendar to create the notification
            channel for.
        webhook_url (str): The URL to which notifications will be sent.
        auth_token (str): The OAuth 2.0 token for authorization.
        channel_id (str): A unique identifier for the notification channel.
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


def validate_post_request(time_now) -> str:
    """
    Allow only POST method.
    """
    global Last_update_timestamp
    time_now_minus_x_seconds = time_now - datetime.timedelta(seconds=1)
    if Last_update_timestamp > time_now_minus_x_seconds:
        return 208
    if request.method == 'POST':
        # print(f"Full headers: {request.headers}")  # Keep for debugging
        resource_state = request.headers.get('X-Goog-Resource-State')
        Last_update_timestamp = time_now
        return resource_state
    else:
        return 405


def time_now_minus_seconds(time_now: datetime, seconds: int=10) -> datetime:
    """
    Checks actual time and subtract from it 10 seconds.
    It's used for getting list of events.
    """
    now_minus_x_seconds = time_now - datetime.timedelta(seconds=seconds)
    return now_minus_x_seconds


def time_now_minus_seconds_iso(time_now: datetime, seconds: int=10) -> str:
    return time_now_minus_seconds(time_now, seconds).isoformat()


def get_event_response_status(event: dict, email) -> str:
    """
    Get invitation response status if there are attendees.

    Returns:
        - 'needsAction' - invitation not accepted (default) ->
            create a new event
        - 'declined' - invitation declined ->
            delete the event (it was created when the invitation was received)
        - 'tentative' - the invitation is being considered ->
            do nothing (event already created)
        - 'accepted' - invitation accepted ->
            do nothing (event already created)
    """
    try:
        attendees = event.get('attendees')
        response_status = ''
        if attendees is not None:
            for attendee in attendees:
                if attendee['email'] == email:
                    return attendee.get('responseStatus')
                else:
                    continue
        return response_status
    except Exception as e:
        print(f"Exception getting response status: {e}")
        return None


def delete_event(calendar_id: str, event_id: str, target_service, target_event) -> None:
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
        print(target_event)
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
        dict: The event data from the target calendar if it exists.
        None: If the event does not exist in the target calendar.
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
    - "htmlLink", "creator" (Read only), "organizer", "iCalUID", "sequence": These are informational fields that do not affect event functionality.

    Args:
        event_data (EventData): An instance of the EventData class containing event details.
    """
    data_to_pop = ("recurringEventId", "kind", "created", "updated", "etag", "creator",
                   "originalStartTime", "htmlLink", "iCalUID", "sequence")
    # "organizer",
    try:
        event_data.data = {
            key: value for key, value in event_data.data.items() if key not in data_to_pop}
    except Exception as e:
        print(f"Exception pop_unnecessary_keys: {e}")


def get_nested_property(data, keys, default=None):
    """
    Utility function to safely extract nested properties from a dictionary.
    """
    for key in keys:
        data = data.get(key, default)
        if data is default:
            break
    return data


def check_event_origin(data: dict, string: str) -> bool:
    """
    Check if the event is created by the user or is a guest event.
    If returns None that means event is original event or key is just missing.
    If it is a copy then it should have extendedProperties with 'note' key.
    """
    ext_properties_note = get_nested_property(
        data, ['extendedProperties', 'shared', 'note'])
    string_to_compare = f"Event copied from {string}"
    if ext_properties_note == None:
        return None
    elif string_to_compare == ext_properties_note:
        return True
    else:
        return False


def event_prefix(summary: str) -> str:
    """
    Get prefix from summary and check if it's in the PREFIXES dictionary.
    Returns None if prefix is not in the dictionary.
    Returns the key from the dictionary if prefix is in the dictionary.
    """
    summary_prefix_len = summary.find("]") + 1
    if summary_prefix_len == 0:
        return None
    summary_prefix = summary[:summary_prefix_len].upper()
    for key in PREFIXES:
        if summary_prefix == key:
            return key


def get_id(id: str) -> str:
    """
    Check if id has '_' in it.
    Depend on the position it is it can be:
    - made from mobile - '_xxxxxxxx_xxxxxx'
    - all-day recurrence - 'xxxxxx_20250401
    - recurrence - 'xxxxxx_20250401T200000Z
    
    Args:
        - id (str): String to check

    Returns:
        - str: id to use as target event id
    """
    position = id.find("_")
    # If position = -1, then '_' is not in string
    if position == -1:
        return id
    # If position = 0, then it's mobile. Replace "_"
    if position == 0:
        id = id.replace("_", "")
        return id
    id_len = len(id)
    after_underscore = id[position+1:id_len]
    after_underscore_len = len(after_underscore)
    after_underscore_all_digits = after_underscore.isdigit()
    # If after "_" is 8 digits then it's all-day recurrence
    if after_underscore_len == 8 and after_underscore_all_digits:
        id = id[:position]
        return id
    # If ater "_" is 16 digits and has "T" and "Z" then it's recurrence
    if after_underscore_len == 16 and id[position + 9] == 'T' and id[position + 16] == 'Z':
        id = id[:position]
        return id
    else:  
        id = id.replace("_", "")
        return id

def get_event_details(event: dict, event_data: EventData, target_event: dict, change_id: bool = False):
    """
    Retrieves details of a specific event and updates instance of class EventData.data.

    Args:
        event (dict): The event data from Google Calendar.
        event_data (EventData): An instance of EventData to store the event details.
        target_event (dict): The event data from the target calendar, used to compare and update details.
        change_id (bool): A flag indicating whether to modify the event ID to remove recurrence-specific timestamps.
                Only used here when new event is created.
    """
    try:
        """
        Get iCalUID instead of id, because id for recurrence get "id_timestamp"
        which is different for all-day event and for not all-day event.
        Beginning of id and iCalUID is the same. iCalUID has at the end @google.com so it has to be removed.
        Uncomment # data if you want to manualy change them."""
        event_data.data = event

        if change_id:
            id = get_id(event.get('id'))
            event_data.data.update({"id": id})

        summary = event.get('summary')
        summary_prefix = event_prefix(summary)

        # Check if event exist in target calendar.
        # If yes then check if summary prefix is:
        # - the same in main and target calendar then copy summary:
        #   - colorId = 0 if prefix is same as default in target calendar
        #   - colorId = from PREFIXES if prefix is not same as default in target calendar
        # - the same as default in target calendar but target calendar doesn't have prefix then copy summary without prefix and colorId = 0 (this means in target calendar is original event without prefix)
        # - not in the PREFIXES then add default prefix and colorId = default
        # else event doesn't exists -> add default prefix is it's not been added already

        color_id = "0"
        first_key = next(iter(PREFIXES))
        if target_event:
            # First copy extended properties from target event to event data.
            # It ensures that this property stays the same in target calendar.
            # Check which event is a copy and which is original.
            # Works only after extended properties were added.
            # If check_event_origin == None, then it's original because extended properties can't be overwritten
            event_is_a_copy = check_event_origin(event, TARGET_CALENDAR_ID)
            if event_is_a_copy == None:
                event_is_a_copy = False
            target_event_is_a_copy = check_event_origin(
                target_event, CALENDAR_ID)
            if target_event_is_a_copy == None:
                target_event_is_a_copy = False
            print(
                f"Event is a copy: {event_is_a_copy}. Target event is a copy: {target_event_is_a_copy}")
            # Check if prefix should be added.
            target_event_summary = target_event.get('summary')
            target_summary_prefix = event_prefix(target_event_summary)
            # Means that in main calendar is original with prefix (PREFIXES[0])
            if summary_prefix == list(PREFIXES)[0] and target_summary_prefix == list(PREFIXES)[0]:
                summary = summary
                color_id = PREFIXES[target_summary_prefix]
            # Means that in target calendar is original event with prefix (PREFIXES[1])
            elif summary_prefix == list(PREFIXES)[1] and target_summary_prefix == list(PREFIXES)[1]:
                summary = summary
                color_id = "0"
            # Means that in target calendar is original event without prefix (PREFIXES[1])
            elif summary_prefix == list(PREFIXES)[1] and target_summary_prefix == None:
                # Remove prefix from summary
                summary_prefix_len = summary.find("]") + 1
                summary = summary[summary_prefix_len + 1:]
                color_id = "0"
            # Means that prefix is not in the summary (original event in main calendar)
            elif summary_prefix == None and target_summary_prefix == list(PREFIXES)[0]:
                summary = first_key + " " + summary
                color_id = PREFIXES[first_key]
            elif summary_prefix == target_summary_prefix:
                summary = summary
                color_id = event.get('colorId')
            else:
                # Something else, so copy as it is
                summary = summary
                color_id = "0"
        else:  # Means that event doesn't exist in target calendar.
            if summary_prefix not in list(PREFIXES.keys()):
                summary = first_key + " " + summary
                color_id = PREFIXES[first_key]
            else:
                for key, value in PREFIXES.items():
                    if key == summary_prefix:
                        summary = summary
                        if key == first_key:
                            color_id = "0"
                        else:
                            color_id = value
                        break

        event_data.data.update({"summary": summary})
        event_data.data.update({"colorId": color_id})

        if VISIBILITY != "YOUR_DATA":
            event_data.data.update({"visibility": VISIBILITY})

        pop_unnecessary_keys(event_data)

        return
    except Exception as e:
        print(
            f"Error getting event details for event {event.get('id')}: {e}. Event details: {event}")
        return None


def create_extended_properties(event_id: str, time_now: datetime, event_is_a_copy: bool=False) -> None:
    if event_is_a_copy:
        calendar_id = TARGET_CALENDAR_ID
    else:
        calendar_id = CALENDAR_ID
    extended_properties = {
        'shared': {
            'note': f'Event copied from {calendar_id}',
            'timestamp': time_now.isoformat(),
            'originalID': event_id
        }
    }
    return extended_properties


def add_extended_properties(extended_properties: dict, event_data: EventData) -> None:
    event_data.data.update(
        {"extendedProperties": extended_properties})


def check_timestamp(event: dict, time_now: datetime):
    """
    Check if timestamp is smaller than now minus 10 seconds.
    If yes then return True -> update event.
    If no then return False -> skip.
    If no timestamp in event data then return None.
    """
    try:
        timestamp = event.get('extendedProperties', {}).get(
            'shared', {}).get('timestamp')
        if timestamp:
            timestamp = datetime.datetime.fromisoformat(timestamp)
            if timestamp < time_now_minus_seconds(time_now, 10):
                return True
            else:
                return False
        else:
            return None
    except Exception as e:
        print(f"Error checking timestamp: {e}")
        return False


def update_extended_properties_timestamp(event_data: EventData, time_now: datetime) -> None:
    """
    Updates the timestamp in the extended properties of the event data.

    Args:
        event_data (EventData): An instance of EventData containing the event details.
        time_now (datetime):  The current time in UTC."""
    try:
        if 'extendedProperties' in event_data.data and 'shared' in event_data.data['extendedProperties']:
            event_data.data['extendedProperties']['shared'].update(
                {'timestamp': time_now.isoformat()})
        else:
            event_data.data.setdefault('extendedProperties', {}).setdefault(
                'shared', {}).update({'timestamp': time_now.isoformat()})
    except Exception as e:
        print(f"Error updating timestamp: {e}")


def create_new_event(calendar_id: str, event_data: EventData, service, time_now) -> None:
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
    print(f"Creating event data: {event_data.data}")
    try:
        event = service.events().insert(calendarId=calendar_id,
                                        body=event_data.data, conferenceDataVersion=1, supportsAttachments=True, sendUpdates='none').execute()
        print(
            f"Event created: {event.get('htmlLink')}\n{event_data.data}\n")
    except Exception as e:
        print(f"Error creating event: {e}")


def update_event(target_service, event_data: EventData, target_event_id: str) -> None:
    """
    Updates event in target calendar.

    Args:
    - target_service: The Google Calendar API service instance used to interact with the calendar.
    - event_data: An instance of EventData containing the event details to update.
    - target_event: A dictionary representing the event data from the target calendar. 
    """
    try:
        target_service.events().update(calendarId=TARGET_CALENDAR_ID,
                                       eventId=target_event_id, body=event_data.data, conferenceDataVersion=1, supportsAttachments=True, sendUpdates='none').execute()
        print(
            f"Event: {event_data.data.get('summary', 'No summary')}, ID: {target_event_id} has been updated.")
    except Exception as e:
        print(
            f"Error updating event {event_data.data.get('summary', 'No summary')}, {target_event_id}: {e}")
        return


def patch_event(service, event_data: EventData, event_id, calendar_id) -> None:
    """
    Updates event in target calendar.

    Args:
    - target_service: The Google Calendar API service instance used to interact with the calendar.
    - event_data: An instance of EventData containing the event details to update.
    - target_event: A dictionary representing the event data from the target calendar. 
    """
    try:
        service.events().patch(calendarId=calendar_id,
                               eventId=event_id, body=event_data.data, conferenceDataVersion=1, supportsAttachments=True, sendUpdates="none").execute()
        print(
            f"Event: {event_data.data.get('summary', 'No summary')}, ID: {event_id} has been patched.\n{event_data.data}")
    except Exception as e:
        print(
            f"Error patching event {event_data.data.get('summary', 'No summary')}, {event_id}: {e}")
        return


def check_calendars_in_attendees(event: dict) -> str:
    """
    Check if both calendars are in the event attendees.

    Args:
        event (dict): list of event attendees.

    Returns:
        - "Both"
        - "Main"
        - "Target"
        - None
        """
    calendar_id_in_attendees = False
    target_calendar_id_in_attendees = False
    try:
        attendees = event.get('attendees', False)
        print(f"Attendees: {attendees}")
        if attendees:
            for attendee in attendees:
                if attendee.get('email', 'no email') == CALENDAR_ID:
                    calendar_id_in_attendees = True
                if attendee.get('email', 'no email') == TARGET_CALENDAR_ID:
                    target_calendar_id_in_attendees = True
            if calendar_id_in_attendees and target_calendar_id_in_attendees:
                return "Both"
            if calendar_id_in_attendees and not target_calendar_id_in_attendees:
                return "Main"
            if not calendar_id_in_attendees and target_calendar_id_in_attendees:
                return "Target"
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"Error checking attendees {e}")
        return None


def check_original_id(event_id: str, event_data: dict, event_is_a_copy: bool) -> str:
    ext_properties_id = get_nested_property(
        event_data, ['extendedProperties', 'shared', 'originalID'])
    if event_is_a_copy == False or event_is_a_copy == None:
        # If ext_properties_id is None then it means that event is original event and target event does't exists.
        # If event is a copy then it should have originalID in extended properties.
        if ext_properties_id is None:
            # "This is original event. Maybe remove _ for target to create."
            return event_id
        else:
            # "This is original event. Maybe remove _ for target to update."
            return ext_properties_id
    else:
        # In extended properties is target event id.
        # If it's a copy so You can only update it.
        # "This is copy event. Returned ID is ok for target."
        return ext_properties_id


def event_created(event: dict, email) -> bool:
    creator = event.get('creator', {}).get('email', {})
    if creator == email:
        return True
    else:
        return False


@app.route('/notifications', methods=['POST'])
def notifications():
    """
    Handles incoming notification messages from the Google Calendar API.
    """
    time_now = datetime.datetime.now(datetime.timezone.utc)
    resource_state = validate_post_request(time_now)
    if resource_state == 405:
        print("405 - Method Not Allowed")
        return "Method Not Allowed", 405
    if resource_state == 208:
        # print("208 - Already Reported")
        return "Already Reported", 208
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
                now_minus_ten_seconds_iso = time_now_minus_seconds_iso(
                    time_now=time_now, seconds=10)
                events_result = service.events().list(calendarId=CALENDAR_ID,
                                                      updatedMin=now_minus_ten_seconds_iso,
                                                      singleEvents=False, maxResults=250, pageToken=page_token).execute()
                events = events_result.get('items', [])
                if events:
                    for event in events:
                        # For debugging print whole event.
                        print(f"Checking event: {event}")
                        # If two way change is disabled and event is a copy then skip it.
                        event_is_a_copy = check_event_origin(
                            event, TARGET_CALENDAR_ID)
                        # if event_is_a_copy == None:
                        #     event_is_a_copy = False
                        if TWO_WAY_CHANGE == False and event_is_a_copy == True:
                            print("Event copied from main calendar. Skip.")
                            continue
                        # Skip events that are not default.
                        event_type = event.get('eventType')
                        if event_type == 'workingLocation' or event_type == 'birthday' or event_type == 'outOfOffice' or event_type == 'focusTime':
                            print(
                                "Event type: working location or birthday or outOfOffice. Skip.")
                            continue
                        event_id = event.get('id')
                        status = event.get('status')
                        response_status = get_event_response_status(
                            event, CALENDAR_ID)
                        original_id = check_original_id(event_id, event, event_is_a_copy)
                        if event_is_a_copy == True:
                            target_event_id = original_id
                        else:
                            target_event_id = get_id(original_id)
                        target_event = check_if_id_exists_in_target_calendar(
                            target_event_id, target_service)
                        event_created_by_calendar_id = event_created(event, CALENDAR_ID)
                        print(f"Event created by calendar id: {event_created_by_calendar_id}.")
                        if target_event:
                            target_event_created_by_target_calendar_id = event_created(target_event, TARGET_CALENDAR_ID)
                        else:
                            target_event_created_by_target_calendar_id = False
                        if event_is_a_copy == False and target_event is None:
                            # So you need to create new event I should not be checking it
                            # target_event_id = event_id
                          if event_is_a_copy == False and target_event is not None:
                              # You should update it.
                              target_event_id = get_id(event_id)
                        event_data = EventData()
                        # Check if target event extended properties are the same as in main calendar.
                        # If empty in target, then copy them from main calendar.
                        # If not empty then check if timestamp is older than 10 seconds.
                        # If not then skip it. If yes then check further.
                        if target_event and status != 'cancelled':
                            target_event_timestamp = target_event.get('extendedProperties', {}).get(
                                'shared', {}).get('timestamp', None)
                            event_timestamp = event.get('extendedProperties', {}).get(
                                'shared', {}).get('timestamp', None)
                            print(
                                f"Target timestamp: {target_event_timestamp}. Event timestamp: {event_timestamp}.")
                            # I left it for further development. Code:
                            # if target_event_timestamp > event_timestamp:
                            #     print(
                            #         f"Target timestamp: {target_event_timestamp} is newer than event timestamp: {event_timestamp}. Skip.")
                            #     continue
                            if check_timestamp(event, time_now) == False:
                                print(
                                    f"Timestamp is not older than 10 seconds. Skip.")
                                continue
                        # Check if CALENDAR_ID and TARGET_CALENDAR_ID are attendees in event.
                        check_attendees = check_calendars_in_attendees(event)
                        if check_attendees == "Both":
                            print("Both calendars are in the event. Skip.")
                            continue
                        # Check if event exists in target calendar - needed to know if it should be updated or created.
                        # Also if event exists, then check summary prefixes - used in get_event_details function.
                        # Status -  status of the event. # Response status - status of the invitation (what attendee did).
                        # Check attendees and status.
                        if target_event and check_attendees == "Main":
                            target_status = target_event.get('status')
                            # target_event_id = target_event.get('id') # Using something else
                            target_response_status = get_event_response_status(
                                target_event, TARGET_CALENDAR_ID)
                            # If event was cancelled, check if target event was declined.
                            # If yes the leave it be. It means that other aplication deleted event becasue original event was declined.
                            if status == 'cancelled' and target_response_status == 'declined':
                                print(
                                    f"Event status: {status} and target event status: {get_event_response_status(target_event)}. Skip.")
                                continue
                            # If event was declined then delete it from target calendar.
                            if response_status == 'declined':
                                print(f"Event was declined. Deleting event.")
                                delete_event(TARGET_CALENDAR_ID,
                                             target_event_id, target_service, target_event)
                                continue
                            # If event was cancelled then delete target event.
                            if status == 'cancelled':
                                print(
                                    f"Event status: {status}. Deleting event.")
                                delete_event(TARGET_CALENDAR_ID,
                                             target_event_id, target_service, target_event)
                                continue
                            if response_status == 'accepted' and target_status == 'cancelled':
                                print(
                                    f"Event response status: {response_status} and target event status: {target_status}. Updating event.")
                                extended_properties = create_extended_properties(original_id, time_now, event_is_a_copy)
                                if event_created_by_calendar_id:
                                    event_data_patched = EventData()
                                    add_extended_properties(
                                        extended_properties, event_data_patched)
                                    patch_event(service, event_data_patched,
                                                event_id, CALENDAR_ID)
                                if target_event_created_by_target_calendar_id:
                                    get_event_details(
                                        event, event_data, target_event)
                                    update_extended_properties_timestamp(
                                        event_data, time_now)
                                    update_event(target_service,
                                                event_data, target_event_id)
                                continue
                            if response_status == 'accepted' and target_status != 'confirmed':
                                print(
                                    f"Event response status: {response_status} and target event status: {target_status}. Patching event.")
                                extended_properties = create_extended_properties(original_id, time_now, event_is_a_copy)
                                if event_created_by_calendar_id:
                                    event_data_patched = EventData()
                                    add_extended_properties(
                                        extended_properties, event_data_patched)
                                    patch_event(service, event_data_patched,
                                                event_id, CALENDAR_ID)
                                if target_event_created_by_target_calendar_id:
                                    event_data.data.update({"status": "confirmed"})
                                    update_extended_properties_timestamp(
                                        event_data, time_now)
                                    patch_event(target_service, event_data,
                                                target_event_id, TARGET_CALENDAR_ID)
                                continue
                            if response_status == 'tentative' and target_status != 'tentative':
                                print(
                                    f"Event response status: {response_status} and target event status: {target_status}. Patching event.")
                                extended_properties = create_extended_properties(original_id, time_now, event_is_a_copy)
                                if event_created_by_calendar_id:
                                    event_data_patched = EventData()
                                    add_extended_properties(
                                        extended_properties, event_data_patched)
                                    patch_event(service, event_data_patched,
                                                event_id, CALENDAR_ID)
                                if target_event_created_by_target_calendar_id:
                                    event_data.data.update({"status": "tentative"})
                                    update_extended_properties_timestamp(
                                        event_data, time_now)
                                    patch_event(target_service, event_data,
                                                target_event_id, TARGET_CALENDAR_ID)
                                continue
                            if target_status != status:
                                print(f"Target_status: {target_status}. Event status: {status}.")
                                extended_properties = create_extended_properties(original_id,time_now, event_is_a_copy)
                                if event_created_by_calendar_id:    
                                    event_data_patched = EventData()
                                    add_extended_properties(
                                        extended_properties, event_data_patched)
                                    patch_event(service, event_data_patched,
                                                event_id, CALENDAR_ID)
                                if target_event_created_by_target_calendar_id:
                                    event_data.data.update({"status": status})
                                    update_extended_properties_timestamp(
                                        event_data, time_now)
                                    patch_event(target_service, event_data,
                                                target_event_id, TARGET_CALENDAR_ID)
                                continue
                        # If event was cancelled then delete target event.
                        # First check if in target event is attendee with email = TARGET_CALENDAR_ID and not CALENDAR_ID.
                        target_check_attendees = None
                        if target_event:
                            target_check_attendees = check_calendars_in_attendees(
                                target_event)
                            print(f"Target attendees: {target_check_attendees}")
                        if status == 'cancelled' and target_check_attendees == "Target":
                            print(
                                f"Event status: {status}. Attendee = Target. Skip")
                            continue
                        if status == 'cancelled':
                            print(
                                f"Event status: {status}. Deleting event.")
                            delete_event(TARGET_CALENDAR_ID,
                                         event_id, target_service, target_event)
                            continue
                        if target_event == None and status != 'cancelled' and response_status != 'declined':
                            print(f"Target event: {target_event}. Creating new event.")
                            extended_properties = create_extended_properties(original_id, time_now, event_is_a_copy)
                            if event_created_by_calendar_id:   
                                event_data_patched = EventData()
                                add_extended_properties(
                                    extended_properties, event_data_patched)
                                patch_event(service, event_data_patched,
                                            event_id, CALENDAR_ID)
                            get_event_details(event, event_data, target_event, change_id=True)
                            add_extended_properties(extended_properties, event_data)
                            create_new_event(TARGET_CALENDAR_ID, event_data, target_service, time_now)
                            continue
                        else:
                            print(f"Last check. Updating event.")
                            extended_properties = create_extended_properties(original_id, time_now, event_is_a_copy)
                            if event_created_by_calendar_id:
                                event_data_patched = EventData()
                                add_extended_properties(
                                    extended_properties, event_data_patched)
                                patch_event(service, event_data_patched,
                                            event_id, CALENDAR_ID)
                            if target_event_created_by_target_calendar_id:
                                get_event_details(
                                    event, event_data, target_event)
                                update_extended_properties_timestamp(
                                    event_data, time_now)
                                update_event(target_service,
                                            event_data, target_event_id)
                            continue
                page_token = events_result.get('nextPageToken')
                if not page_token:
                    break
        except Exception as e:
            print(f"Error listing events: {e}")
    return "OK", 200


# --- Run the channel creation when the app starts ---
# with app.app_context():
#     create_token()
#     create_notification_channel(
#         CALENDAR_ID, WEBHOOK_URL, AUTH_TOKEN, CHANNEL_ID)


# --- Run the Flask app ---
if __name__ == '__main__':
    app.run()
