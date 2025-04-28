import datetime
CALENDAR_ID = "test@gmail.com"
# time_now = datetime.datetime.now(datetime.timezone.utc)
time_now = "20250422T12:00:00Z"

extended_properties = {
    'extendedProperties': {
        'shared': {
            'note': f'Event copied from {CALENDAR_ID}',
            # 'timestamp': time_now
        }
    }}

print(extended_properties)


time_now = "3330422T12:00:00Z"

if 'extendedProperties' in extended_properties and 'shared' in extended_properties['extendedProperties']:
    extended_properties['extendedProperties']['shared'].update(
        {'timestamp': time_now})
else:
    extended_properties.setdefault('extendedProperties', {}).setdefault('shared', {}).update({
        'timestamp': time_now})

print(extended_properties)


EVENT_1 = {
    'kind': 'calendar#event',
    'etag': '"3488766735517150"',
    'id': '7khhiebcq22i04sueovmvk6rf4',
    'status': 'confirmed',
    'htmlLink': 'https://www.google.com/calendar/event?eid=N2toaGllYmNxMjJpMDRzdWVvdm12azZyZjQgc2xhd29taXIud29sa0Bib3RsYW5kLmNvbS5wbA',
    'created': '2025-04-11T14:47:05.000Z',
    'updated': '2025-04-11T14:56:07.758Z',
    'summary': 'TEST-Kosz',
    'creator': {'email': 'test@gmail.com', 'self': True},
    'organizer': {'email': 'test@gmail.com', 'self': True},
    'start': {'dateTime': '2025-04-15T17:00:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'end': {'dateTime': '2025-04-15T17:45:00+02:00', 'timeZone': 'Europe/Warsaw'},
    'iCalUID': '7khhiebcq22i04sueovmvk6rf4@google.com',
    'sequence': 4,
    'reminders': {'useDefault': True},
    'eventType': 'default',
    'attendees': [{'email': 'test@gmail.com', 'organizer': True, 'responseStatus': 'accepted'},
                  {'email': 'some_mail@domain.pl', 'responseStatus': 'accepted'}],
}

# time_plus_10 = time_now + datetime.timedelta(seconds=10)
# timestamp = time_now.isoformat()
# timestamp_10 = time_plus_10.isoformat()
# print(timestamp, timestamp_10)
# print(time_now < time_plus_10)


# def piec():
#     return 5




    # To coś poniżej
# if id.find("_") == -1:
#     id = id
# This:
id = '6f6cnrcko224327gbu1ihb9tc2_20250425T200000Z'
position = id.find('_')
print(position)
print(position + 9)
if id[position + 9] == 'T':
    print("T jest")
else:
    print("T nie jest")
if id[position + 16] == 'Z':
    print("Z jest")
else:
    print("Z nie jest")

# Or that:
id = 'tc2_20250425T200000Z'
position = id.find('_')
end = id[position+1:len(id)]
print(end)
z = end.isdigit()
print(z)
# Then its recurrence
# If not then id.replace("_")

id_len = len(id)
print(position)
print(id_len)
print(id_len - position)


# import pathlib
# config_path = pathlib.Path("config.ini").parent.absolute()
# print(f"CPATH: {config_path}")
# import configparser
# import os
# config = configparser.ConfigParser()
# file_config_path = os.path.join(os.getcwd(),)
# print(f"File path: {config_path}")
# config.read(config_path)
# print(f"Config1: {config}")
# print(f"Config: {config.sections()}")
# PREFIXES = config.get('configuration', 'PREFIXES')
# print(PREFIXES)

def get_nested_property(data, keys, default=None):
    """
    Utility function to safely extract nested properties from a dictionary.
    """
    for key in keys:
        data = data.get(key, default)
        if data is default:
            break
    return data

print("Check Event origin")
# def check_event_origin(data: dict, string: str) -> bool:
#     """
#     Check if the event is created by the user or is a guest event.
#     If returns None that means event is original event or key is just missing.
#     If it is a copy then it should have extendedProperties with 'note' key.
#     """
ext_properties_note = get_nested_property(EVENT_1, ['extendedProperties', 'shared', 'note'])
print(ext_properties_note)
if ext_properties_note:
    print(True)
else:
    print(False)

from datetime import datetime
print(datetime(2025, 4, 1, 21, 37).isoformat())