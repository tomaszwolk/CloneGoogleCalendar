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
from dateutil.parser import parse
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


# For PREFIXES first key in dictionary is default key for main calendar.
# Second key is default for target calendar.
PREFIXES = {
    "[BTL]": "9",
    "[MKS]": "7",
    "[ADSO]": "9",
}

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
deleted_event_list_id = []
event_list_id = []


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


def check_recurrence(event: dict) -> bool:
    """
    Check if the event is recurring by checking if the 'recurringEventId' key is present in the event object."""
    if event.get('recurringEventId') != None:
        return True
    else:
        return False


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
    if event_id in deleted_event_list_id:
        return
    try:
        target_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        deleted_event_list_id.append(event_id)
        print(f"Event ID: {event_id} deleted")
        return
    except Exception as e:
        print(f"Error deleting event {event_id}: {e}.")
        return None


def check_if_id_exists_in_target_calendar(event_id: str, target_service) -> dict:
    """
    Extracts the portion of the ID before the first underscore, if present.
    If no underscore is found, returns the original ID.

    Args:
        id (str): The event ID.
        target_service: The Google Calendar API service instance used to interact with the calendar.

    Returns:
        dict:   {
                EventBody: None if event doesn't exist in target calendar else event body,
                ToDo: "Create new event" if event doesn't exist in target calendar else "Update" or "Update to recurrence",
                target_sequence: None if event doesn't exist in target calendar else sequence of the event in target calendar.
                }.
    """
    try:
        target_event = target_service.events().get(calendarId=TARGET_CALENDAR_ID,
                                                   eventId=event_id).execute()
        # print(f"Event {event_id} exists in target calendar.")
        target_sequence = target_event.get('sequence')
        return {"EventBody": target_event, "ToDo": "Update", "target_sequence": target_sequence}
    except HttpError as error:
        try:
            event_id = get_id(event_id)
            target_event = target_service.events().get(calendarId=TARGET_CALENDAR_ID,
                                                       eventId=event_id).execute()
            # print(f"Event {event_id} exists in target calendar.")
            target_sequence = target_event.get('sequence')
            return {"EventBody": target_event, "ToDo": "Update to recurrence", "target_sequence": target_sequence}
        except HttpError as error:
            return {"EventBody": None, "ToDo": "Create new event", "target_sequence": None}


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


def get_id(id: str) -> str:
    """
    Removes timeStamp added to id after symbol "_" when event is reccurrence.
    """
    position = id.find("_")
    if position == -1:
        id = id
    else:
        id = id[:position]
    return id


def get_event_details(event: dict, event_data: dict, target_event: dict, change_id: bool):
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

        id = event.get('id')
        if change_id:
            id = get_id(id)
        event_data.data.update({"id": id})

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

        # visibility = "private" # option
        # event_data.data.update({"visibility": visibility})

        pop_unnecessary_keys(event_data)

        return
    except Exception as e:
        print(
            f"Error getting event details for event {event.get('id')}: {e}. Event details: {event}")
        return None


def count_difference_in_days(events: list) -> int:
    """
    Counts difference in days for first two events in events list.
    Function is used only if recurrence is True.
    """
    if all_day_event(events[0]):
        first_event_start = events[0].get('start').get('date')
        second_event_start = events[1].get('start').get('date')
    else:
        first_event_start = events[0].get('start').get('dateTime')
        first_event_start = first_event_start[:10]
        second_event_start = events[1].get('start').get('dateTime')
        second_event_start = second_event_start[:10]
    first_event_start = parse(first_event_start)
    second_event_start = parse(second_event_start)
    difference_in_days = second_event_start - first_event_start
    difference_in_days = difference_in_days.days
    return difference_in_days


def recurrence_data(events: list, event_data: dict) -> None:
    """
    Checks what frequency and how many recurring events are being created.
    Updates event_data.data (instance of class EventData).
    """
    difference_in_days = count_difference_in_days(events)
    if difference_in_days == -1:
        return
    interval = 1  # default value
    match difference_in_days:
        case 1:
            frequency = "DAILY"
        case _ if 7 > difference_in_days > 1:
            frequency = "DAILY"
            interval = difference_in_days
        case 7:
            frequency = "WEEKLY"
        case 14:
            frequency = "WEEKLY"
            interval = 2
        case 21:
            frequency = "WEEKLY"
            interval = 3
        case 28:
            frequency = "WEEKLY"
            interval = 4
        case 35:
            frequency = "WEEKLY"
            interval = 5
        case _ if 360 > difference_in_days > 7:
            frequency = "MONTHLY"
        case _ if difference_in_days > 360:
            frequency = "YEARLY"

    # If count=250 (max what API gives you at one chunk) then it's infinity
    count = len(events)
    if count == 250:
        recurrence_rule = [
            f"RRULE:FREQ={frequency};INTERVAL={interval}"]
    else:
        recurrence_rule = [
            f"RRULE:FREQ={frequency};INTERVAL={interval};COUNT={count}"]
    event_data.data.update({"recurrence": recurrence_rule})
    return


def all_day_event(event: dict) -> bool:
    """Check if all-day event. If yes returns True. For all day event 'dateTime' is None."""
    start = event.get('start').get('dateTime')
    end = event.get('end').get('dateTime')
    if start == None and end == None:
        return True
    else:
        return False


def create_new_event(calendar_id: str, event_data: EventData, service) -> None:
    """
    Creates a new event in the specified calendar.

    Args:
        - calendar_id: The ID of the calendar to create the event in (CALENDAR_ID_TO_ADD).
        - event_data: An instance of EventData
        - service: The Google Calendar API service instance used to interact with the calendar.
    """
    if event_data.data.get('id') in event_list_id:
        print("Not creating event. Event already exists in target calendar.")
        return
    try:
        event = service.events().insert(calendarId=calendar_id,
                                        body=event_data.data, conferenceDataVersion=1, supportsAttachments=True).execute()
        print(
            f"Event created: {event.get('htmlLink')}\n{event_data.data}\n")
        event_list_id.append(event_data.data.get('id'))
    except Exception as e:
        print(f"Error creating event: {e}")


def updated_after_target_calendar(event: dict, event_id: str, target_service) -> bool:
    """
    Check if event was already updated.
    Because several webhooks are being received it won't unnecessary call functions.
    """
    # Timestamp of variable 'updated' in primary calendar
    event_updated = parse(event.get('updated'))
    # Timestamp of variable 'updated' in target calendar
    target_event = target_service.events().get(
        calendarId=TARGET_CALENDAR_ID, eventId=event_id).execute()
    target_event_updated = parse(target_event.get('updated'))

    time_between_updates = event_updated - target_event_updated
    if time_between_updates > datetime.timedelta(seconds=0):
        return True
    else:
        # print("Event already updated")
        return False


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
            while True:
                page_token = None
                # Retrieve the list of events from the master calendar that has been changed in last 10 seconds
                now_minus_ten_seconds_iso = time_now_minus_ten_seconds()
                events_result = service.events().list(calendarId=CALENDAR_ID,
                                                      updatedMin=now_minus_ten_seconds_iso,
                                                      singleEvents=True, maxResults=250, pageToken=page_token).execute()
                events = events_result.get('items', [])
                try:
                    recurrence = check_recurrence(events_result['items'][0])
                except IndexError:
                    break
                if events:
                    for event in events:
                        event_type = event.get('eventType')
                        if event_type == 'workingLocation' or event_type == 'birthday':
                            print("Event type: working location or birthday. Skip.")
                            continue
                        sequence = event.get('sequence')
                        event_id = event.get('id')
                        target_event_dict = check_if_id_exists_in_target_calendar(
                            event_id, target_service)
                        target_event_sequence = target_event_dict["target_sequence"]
                        # if sequence is the same it means that event has not been changed
                        if sequence == target_event_sequence:
                            continue
                        target_event = target_event_dict["EventBody"]
                        # if target_event_data == 404 then target_event = None and don't get target_event_dict
                        event_data = EventData()
                        status = event.get('status')
                        response_status = get_event_response_status(event)
                        if target_event == None and status != 'cancelled' and response_status != 'declined':
                            get_event_details(
                                event, event_data, target_event, change_id=True)
                            if recurrence:
                                recurrence_data(events, event_data)
                            create_new_event(TARGET_CALENDAR_ID,
                                             event_data, target_service)
                            if recurrence:
                                break
                            continue
                        if status == 'cancelled' or response_status == 'declined':
                            print(
                                f"Status: {status}. Response status: {response_status}")
                            delete_event(TARGET_CALENDAR_ID,
                                         event_id, target_service)
                            continue
                        if target_event_dict["ToDo"] == "Update to recurrence":
                            get_event_details(event, event_data,
                                              target_event, change_id=True)
                            recurrence_data(events, event_data)
                            update_event(target_service,
                                         event_data, target_event)
                            break
                        # elif updated_after_target_calendar(event=event, event_id=event_id, target_service=target_service) == True:
                        else:
                            get_event_details(
                                event, event_data, target_event, change_id=False)
                            update_event(target_service,
                                         event_data, target_event)
                            continue
                        # else:
                        #     continue
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
