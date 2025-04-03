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
    - copy all and modyfi summary

Change everywhere 'YOUR_DATA' to your data.
"""

app = Flask(__name__)

# --- Configuration (Replace with your actual values) ---
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
# Replace with your calendar ID, need to be written as e-mail, not as 'primary' (to check 'responseStatus') string
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

AUTH_TOKEN = CREDENTIALS.token
deleted_event_list_id = []
event_list_id = []

# For PREFIXES first key in dictionary is default key for main calendar.
# Second key is default for target calendar.
PREFIXES = {
    "[BTL]": "9",
    "[MKS]": "7",
    "[ADSO]": "9",
}

# --- Load OAuth 2.0 Credentials ---


def load_credentials(token_path: json, credentials: json, credentials_path: json, scopes: list):
    if os.path.exists(token_path):
        credentials = Credentials.from_authorized_user_file(
            token_path, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, scopes
            )
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(credentials.to_json())


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
    now = datetime.datetime.now(datetime.timezone.utc)
    now_minus_ten_seconds = now - datetime.timedelta(seconds=10)
    now_minus_ten_iso = now_minus_ten_seconds.isoformat()
    return now_minus_ten_iso


def check_recurrence(event: dict) -> bool:
    """
    Check if the event is recurring by checking if the 'recurringEventId' key is present in the event object."""
    if event.get('recurringEventId') != None:
        return True
    else:
        return False


def get_event_response_status(event: dict):
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


def delete_event(calendar_id: str, event_id: str, target_service):
    """
    Deletes an event from the specified calendar. Checks if already event has been deleted if not appends id to list.

    Args:
        calendar_id (str): The ID of the calendar from which to delete the event.
        event_id (str): The ID of the event to delete.
        target_service (Resource): The Google Calendar API service instance.
    """
    if event_id in deleted_event_list_id:
        return
    try:
        target_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        deleted_event_list_id.append(event_id)
        print(f"Event ID: {event_id} deleted")
        return
    except Exception as e:
        print(f"Error deleting event: {e}")
        return None


def check_if_id_exists_in_target_calendar(event_id: str, target_service):
    try:
        target_event = target_service.events().get(calendarId=TARGET_CALENDAR_ID,
                                                   eventId=event_id).execute()
        print(f"Event {event_id} exists in target calendar.")
        return target_event
    except HttpError as error:
        print(f"Event {event_id} does not exist in target calendar.")
        return False


def get_event_details(event: dict, event_data: dict, target_event: dict):
    """
    Retrieves details of a specific event and updates instance of class EventData.data.

    Args:
        event (dict): The event data from Google Calendar.
        event_data (EventData): An instance of EventData to store the event details.
    """
    print("Getting event details")
    try:
        """
        Get iCalUID instead of id, because id for recurrence get "id_timestamp"
        which is different for all-day event and for not all-day event.
        Beginning of id and iCalUID is the same. iCalUID has at the end @google.com so it has to be removed.
        Uncomment # data if you want to manualy change them."""
        event_data = event

        id = event.get('iCalUID')
        position = id.find("_")
        if position == -1:
            id = id[:-11]
        else:
            id = id[:position]
        event_data.update({"id": id})

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
        if target_event:
            target_event_summary = target_event.get('summary')
            if summary[:summary_prefix_len] == target_event_summary[:summary_prefix_len] == list(PREFIXES)[1]:
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

        event_data.update({"summary": summary})
        event_data.update({"colorId": color_id})

        # conference_data = event.get('conferenceData')
        # event_data.update({'conferenceData': conference_data})

        # description = event.get('description')
        # event_data.update({"description": description})

        # visibility = event.get('visibility')
        # if visibility is None:
        #     visibility = "default"
        # event_data.update({"visibility": visibility})

        # location = event.get('location')
        # if location is None:
        #     location = ""
        # event_data.update({"location": location})

        # event_type = event.get('eventType')
        # event_data.data.update({'eventType': event_type})

        # attendees = event.get('attendees')
        # event_data.update({'attendees': attendees})

        # if all_day_event(event):
        #     start = event.get('start').get('date')
        #     end = event.get('end').get('date')
        #     event_data.update({"start": {"date": start}})
        #     event_data.update({"end": {"date": end}})
        # else:
        #     start = event.get('start').get(
        #         'dateTime')
        #     end = event.get('end').get('dateTime')
        #     event_data.update(
        #         {"start": {"dateTime": start, "timeZone": "Europe/Warsaw"}})
        #     event_data.update(
        #         {"end": {"dateTime": end, "timeZone": "Europe/Warsaw"}})
        return
    except Exception as e:
        print(f"Error getting event details for event {event.get('id')}: {e}")
        return None


def count_difference_in_days(events: list) -> int:
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

    count = len(events)  # int, if 250 then it's infinity
    if count == 250:
        recurrence_rule = [
            f"RRULE:FREQ={frequency};INTERVAL={interval}"]
    else:
        recurrence_rule = [
            f"RRULE:FREQ={frequency};INTERVAL={interval};COUNT={count}"]
    event_data.update({"recurrence": recurrence_rule})
    return


def all_day_event(event: dict) -> bool:
    """Check if all-day event. If yes returns True. For all day event 'dateTime' is None."""
    start = event.get('start').get('dateTime')
    end = event.get('end').get('dateTime')
    if start == None and end == None:
        return True
    else:
        return False


def create_new_event(calendar_id: str, event_data: dict, service) -> None:
    """
    Creates a new event in the specified calendar.

    Args:
        - calendar_id: The ID of the calendar to create the event in (CALENDAR_ID_TO_ADD).
        - event_data: A dictionary containing the event details - created in get_event_details function.
        - service = build("calendar", "v3", credentials=credentials, cache_discovery=False) - created in notifications function
    """
    try:
        event = service.events().insert(calendarId=calendar_id,
                                        body=event_data, conferenceDataVersion=1).execute()
        print(
            f"Event created: {event.get('htmlLink')}\n{event_data}\n")
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
        print("Event already updated")
        return False


def update_event(event_id: str, service, target_service, event_data: dict):
    event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
    get_event_details(event, event_data)
    target_service.events().update(calendarId=TARGET_CALENDAR_ID,
                                   eventId=event_id, body=event_data, conferenceDataVersion=1).execute()
    print(f"Event: {event_data['summary']}, {event_id} has been updated.")
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
            # Retrieve the list of events from the master calendar that has been changed in last 10 seconds
            now_minus_ten_seconds_iso = time_now_minus_ten_seconds()
            events_result = service.events().list(calendarId=CALENDAR_ID,
                                                  updatedMin=now_minus_ten_seconds_iso,
                                                  singleEvents=True).execute()
            events = events_result.get('items', [])
            if events:
                for event in events:
                    event_type = event.get('eventType')
                    if event_type == 'workingLocation':
                        print("Event type: working location. Skip.")
                        continue
                    status = event.get('status')
                    response_status = get_event_response_status(event)
                    event_id = event.get('id')
                    if status == 'candelled' or response_status == 'declined':
                        print(
                            f"Status: {status}. Response status: {response_status}")
                        delete_event(TARGET_CALENDAR_ID,
                                     event_id, target_service)
                        continue
                    event_data = EventData()
                    target_event = check_if_id_exists_in_target_calendar(
                        event_id, target_service)
                    if not target_event:
                        get_event_details(event, event_data.data, target_event)
                        if check_recurrence(events_result['items'][0]):
                            recurrence_data(events, event_data.data)
                        create_new_event(TARGET_CALENDAR_ID,
                                         event_data.data, target_service)
                        continue
                    elif updated_after_target_calendar(event=event, event_id=event_id, target_service=target_service) == True:
                        update_event(event_id, service,
                                     target_service, event_data.data)
                        continue
                    else:
                        break
            else:
                return
        except Exception as e:
            print(f"Error listing events: {e}")
    return "OK", 200


# --- Run the channel creation when the app starts ---
with app.app_context():
    # Load credentials
    load_credentials(TOKEN_PATH, CREDENTIALS, CREDENTIALS_PATH, SCOPES)
    # Load target credentials
    load_credentials(TARGET_TOKEN_PATH, TARGET_CREDENTIALS,
                     CREDENTIALS_PATH, SCOPES)
    create_notification_channel(
        CALENDAR_ID, WEBHOOK_URL, AUTH_TOKEN, CHANNEL_ID)

# --- Run the Flask app ---
if __name__ == '__main__':
    app.run()
