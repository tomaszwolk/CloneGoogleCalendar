import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import configparser

# app = Flask(__name__)

""" 
--- Configuration (Replace with your actual values) ---
emails are stored in a file called email.txt. Example how file should look like:
[emails]
CALENDAR_ID: "mks.test@mks-meble.pl"
CALENDAR_ID_TO_ADD: "btl.test@botland.com.pl"
"""
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
config = configparser.ConfigParser()
config.read("email.txt")
CALENDAR_ID = config.get("emails", "CALENDAR_ID")
CALENDAR_ID_TO_ADD = config.get("emails", "CALENDAR_ID_TO_ADD")
# --- OAuth 2.0 Credentials (Replace with your actual credentials) ---
# You will need to set up OAuth 2.0 and obtain these credentials
# This is a simplified example, you should store these securely
TOKEN_PATH = "token.json"
TARGET_TOKEN_PATH = "target_token.json"
CREDENTIALS_PATH = "credentials.json"
CREDENTIALS = None
TARGET_CREDENTIALS = None

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

service = build("calendar", "v3", credentials=CREDENTIALS,
                cache_discovery=False)

service = build("calendar", "v3", credentials=TARGET_CREDENTIALS,
                cache_discovery=False)
