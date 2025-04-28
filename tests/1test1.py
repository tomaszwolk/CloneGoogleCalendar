
import datetime
import configparser

# now = datetime.datetime.now(datetime.timezone.utc)
# time_now_minus_5_seconds = now - datetime.timedelta(seconds=5)


# Last_update_timestamp = time_now_minus_5_seconds


# def validate_post_request() -> str:
#     """
#     Allow only POST method.
#     """
#     global Last_update_timestamp
#     now = datetime.datetime.now(datetime.timezone.utc)
#     time_now_minus_5_seconds = now - datetime.timedelta(seconds=5)
#     if Last_update_timestamp < time_now_minus_5_seconds:
#         return (Last_update_timestamp, time_now_minus_5_seconds, abs(Last_update_timestamp-time_now_minus_5_seconds))
#     # if request.method == 'POST':
#     #     # print(f"Full headers: {request.headers}")  # Keep for debugging
#     #     resource_state = request.headers.get('X-Goog-Resource-State')
#     #     Last_update_timestamp = now
#     #     return resource_state
#     else:
#         return 405


# x = validate_post_request()
# print(x)

# summary = "[BTL] This is a test summary"
# summary = "[MKS] This is a test summary"
summary = "[ADSO] This is a test summary"
# summary = "[PRO] This is a test summary"
# summary = "NIC This is a test summary"

summary_prefix_len = summary.find("]") + 1

PREFIXES = {
    "[BTL]": "9",
    "[MKS]": "7",
    "[ADSO]": "9",
}

color_id = "0"
first_key = list(PREFIXES.keys())[0]

# if summary[:summary_prefix_len] == first_key:
#     summary = summary
# elif summary[:summary_prefix_len] in list(PREFIXES.keys()):
#     summary = summary
#     # summary = summary.replace(first_key, first_key + " ", 1)
# elif summary[:summary_prefix_len] in list(PREFIXES.values()):
#     summary = summary.replace(summary[:summary_prefix_len], first_key)
#     summary = summary.replace(first_key, first_key + " ", 1)
# else:
#     summary = first_key + " " + summary
# color_id = PREFIXES[first_key]

# print(summary, color_id)
if summary[:summary_prefix_len] not in list(PREFIXES.keys()):
    summary = first_key + " " + summary
    color_id = PREFIXES[first_key]
else:
    for key, value in PREFIXES.items():
        if key == summary[:summary_prefix_len]:
            summary = summary
            color_id = value
            break
        # else:
        #     summary = first_key + " " + summary
        #     color_id = PREFIXES[first_key]

print(summary, color_id)

config = configparser.ConfigParser()
config.read('CreateToken/email.txt')
var_a = config.get("emails", "CALENDAR_ID")
var_b = config.get("emails", "CALENDAR_ID_TO_ADD")

print(var_a, var_b)

# with open('CreateToken/email.txt', 'r') as file:
#     for line in file:
#         # Split each line into key and value
#         key, value = line.strip().split('=')
#         variables[key] = value

# print(key, value)


events_result = {'kind': 'calendar#event', 'etag': '"3488576213328510"', 'id': '4fovmae4dd0jl588qlu4ggc6cd', 'status': 'confirmed', 'htmlLink': 'https://www.google.com/calendar/event?eid=NGZvdm1hZTRkZDBqbDU4OHFsdTRnZ2M2Y2Qgc2xhd29taXIud29sa0Bib3RsYW5kLmNvbS5wbA', 'created': '2025-04-10T12:28:25.000Z', 'updated': '2025-04-10T12:28:26.664Z', 'summary': '[MKS] Zebranie CEO - COO', 'colorId': '7', 'creator': {'email': 'slawomir.wolk@botland.com.pl', 'self': True}, 'organizer': {
    'email': 'slawomir.wolk@botland.com.pl', 'self': True}, 'start': {'dateTime': '2025-04-11T09:00:00+02:00', 'timeZone': 'Europe/Warsaw'}, 'end': {'dateTime': '2025-04-11T10:00:00+02:00', 'timeZone': 'Europe/Warsaw'}, 'iCalUID': '4fovmae4dd0jl588qlu4ggc6cd@google.com', 'sequence': 0, 'extendedProperties': {'shared': {'note': 'Event copied from slawomir.wolk@mks-meble.pl'}}, 'reminders': {'useDefault': True}, 'eventType': 'default'}


def get_nested_property(data, keys, default=None):
    """
    Utility function to safely extract nested properties from a dictionary.
    """
    for key in keys:
        data = data.get(key, default)
        print(data)
        if data is default:
            break
    return data


ext_pro = get_nested_property(
    events_result, ['extendedProperties', 'shared', 'note'])

print(ext_pro)

pref = "[mkS] sasd"
pref_upper = pref[:5].upper()
print(pref_upper)
for key in PREFIXES:
    if pref_upper == key:
        print(key)
        break

summary = "[MKS] opppo"
summary_prefix_len = summary.find("]") + 1
print(summary_prefix_len)
if summary_prefix_len == 0:
    print("None")
summary_prefix = summary[:summary_prefix_len].upper()
print(len(summary_prefix))
for key in PREFIXES:
    print(key)
    if summary_prefix == key:
        print("1")
        print(key)


attendees = [{'email': 'liberto.testowy@gmail.com', 'organizer': True, 'self': True,
              'responseStatus': 'accepted'}, {'email': 'liberto.testowy2@gmail.com', 'responseStatus': 'needsAction'}]
CALENDAR_ID = "liberto.testowy@gmail.com"
TARGET_CALENDAR_ID = "liberto.testowy2@gmail.com"
for attendee in attendees:
    if attendee.get('email') == TARGET_CALENDAR_ID:
        print("CAL_ID found")
for attendee in attendees:
    if attendee.get('email') == CALENDAR_ID:
        print("CAL_ID found")


time_now = datetime.datetime.now(datetime.timezone.utc)
print(time_now)
print(time_now.isoformat())

time1 = datetime.datetime(2025, 4, 1, 8, 29, 15, 22)
time2 = datetime.datetime(2025, 4, 1, 8, 29, 15, 22)
print(time1 == time2)

event = {'attendees': 
                [{'email': 'me@you.pl', 'organizer': True, 'responseStatus': 'accepted'}, 
                {'email': 'someone@domain.com', 'responseStatus': 'accepted'}, 
                {'email': 'test@gmail.com', 'self': True, 'responseStatus': 'accepted'}, 
                {'email': 'c_18832tc9g2iechoiehr7goqp9bsali@resource.calendar.google.com', 'displayName': 'Biuro (6) [TV+Jabra+Camera]', 'resource': True, 'responseStatus': 'accepted'}],}


attendees = event.get('attendees')
response_status = ''
if attendees is not None:
    for attendee in attendees:
        print(attendee)
        if attendee['email'] == 'test@gmail.com':
            print(attendee.get('responseStatus'))
        else:
            print("nope")

class EventData:
    def __init__(self):
        self.data = {
        }

event = EventData()
print(type(event.data))

print(datetime(2025, 4, 1, 21, 37).isoformat())