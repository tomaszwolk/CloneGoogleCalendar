import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# IMPORTANT this works only with scopes calendar.

# --- Configuration (Replace with your actual values) ---
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = ""
CALENDAR_ID_TO_ADD = ""
# --- OAuth 2.0 Credentials (Replace with your actual credentials) ---
# You will need to set up OAuth 2.0 and obtain these credentials
# This is a simplified example, you should store these securely
TOKEN_PATH = "token.json"
TARGET_TOKEN_PATH = "target_token.json"
CREDENTIALS_PATH = "credentials.json"
CREDENTIALS = None
TARGET_CREDENTIALS = None
CALENDAR_LIST_PATH = "calendar_list.txt"
TARGET_CALENDAR_LIST_PATH = "target_calendar_list.txt"


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


service = build("calendar", "v3", credentials=CREDENTIALS,
                cache_discovery=False)

page_token = None
with open(CALENDAR_LIST_PATH, "w"):
    pass
while True:
    calendar_list = service.calendarList().list(pageToken=page_token).execute()
    for calendar_list_entry in calendar_list['items']:
        calendar_data = f"{calendar_list_entry['summary']}, {calendar_list_entry['id']}, {calendar_list_entry['accessRole']}\n"
        with open(CALENDAR_LIST_PATH, "a") as token:
            token.write(calendar_data)
    page_token = calendar_list.get('nextPageToken')
    if not page_token:
        break


service = build("calendar", "v3", credentials=TARGET_CREDENTIALS,
                cache_discovery=False)

page_token = None
with open(TARGET_CALENDAR_LIST_PATH, "w"):
    pass
while True:
    calendar_list = service.calendarList().list(pageToken=page_token).execute()
    for calendar_list_entry in calendar_list['items']:
        calendar_data = f"{calendar_list_entry['summary']}, {calendar_list_entry['id']}, {calendar_list_entry['accessRole']}\n"
        with open(TARGET_CALENDAR_LIST_PATH, "a") as token:
            token.write(calendar_data)
    page_token = calendar_list.get('nextPageToken')
    if not page_token:
        break
