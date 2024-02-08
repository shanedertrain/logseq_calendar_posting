from datetime import datetime
import tzlocal
import zoneinfo
from pathlib import Path
from dataclasses import dataclass, asdict
from dataclasses import dataclass
from typing import Optional, Union

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import configuration as cfg

FMT_DATETIME = '%Y-%m-%dT%H:%M:%S'

SCOPES = ['https://www.googleapis.com/auth/calendar']

@dataclass
class Event:
    summary: str
    start: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    end: Optional[datetime] = None
    recurrence: Optional[list[str]] = None
    attendees: Optional[list[dict]] = None
    reminders: Optional[dict] = None

    def to_dict(self):
        self.start = {
            'dateTime': self.start.strftime(FMT_DATETIME),
            'timeZone': self.start.tzname()
            }

        if self.end:
            self.end = {
            'dateTime': self.end.strftime(FMT_DATETIME),
            'timeZone': self.end.tzname()
            }

        return asdict(self)

class GoogleCalendar:
    def __init__(self, token_path: Path, credentials_path: Path):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.service = self.initialize_calendar_service()

    def authenticate(self, credentials_path: Path):
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        return creds

    def initialize_calendar_service(self):
        creds = None

        try:
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        except Exception as e:
            cfg.LOGGER.error(f'Error loading credentials: {e}')

        if not creds or not creds.valid:
            creds = self.authenticate(self.credentials_path)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)

    def create_event(self, event: Event):
        local_timezone = tzlocal.get_localzone()

        if event.start.tzinfo == None:
            event.start = event.start.replace(tzinfo=local_timezone)
        
        # If end_time is not provided, set it to be the same as the start time
        if event.end == None:
            event.end = event.start

        if event.end.tzinfo == None:
            event.end = event.end.replace(tzinfo=local_timezone)

        # Check if the event already exists
        if self.event_exists(event):
            cfg.LOGGER.debug(f"Event with summary '{event.summary}' already exists. Not adding duplicate.")
            return False, f"Event with summary '{event.summary}' already exists. Not adding duplicate."

        # Add the event to the calendar
        try:
            self.service.events().insert(calendarId='primary', body=event.to_dict()).execute()
            cfg.LOGGER.info(f"Added to calendar: {event.summary}: {event.start} to {event.end}")
            return True, f"Added to calendar: {event.summary}: {event.start} to {event.end}"
        except HttpError as e:
            cfg.LOGGER.error(f"Error adding {event.summary} to calendar: {e}")
            return False, f"Error adding {event.summary} to calendar: {e}"

    def event_exists(self, event: Event):
        # Check if an event with the same details already exists
        existing_events = self.service.events().list(calendarId='primary').execute().get('items', [])

        for existing_event in existing_events:
            # existing_event_dict = asdict(Event(**existing_event))  # Convert existing event to a dictionary
            if existing_event['status'] != 'cancelled':
                if existing_event['summary'] == event.summary:
                    return True

        return False

if __name__ == '__main__':
    # Specify the token and credentials paths as Path objects
    custom_token_path = cfg.TOKEN_PATH
    custom_credentials_path = cfg.CREDENTIALS_PATH

    # Create an instance of the GoogleCalendar class with custom paths
    google_calendar = GoogleCalendar(token_path=custom_token_path, credentials_path=custom_credentials_path)

    task_title = 'Test Task: Complete Assignment'
    start_datetime = datetime.today()

    event_instance = Event(
        summary=task_title,
        location='800 Howard St., San Francisco, CA 94103',
        description='A chance to hear more about Google\'s developer products.',
        start= start_datetime,
        end=None,
        recurrence=['RRULE:FREQ=DAILY;COUNT=2'],
        attendees=[{'email': 'john@example.com'}, {'email': 'jane@example.com'}],
        reminders={'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 10}]},
    )
    
    # Use the create_event method without passing the service explicitly
    success, message = google_calendar.create_event(event_instance)

    if success:
        cfg.LOGGER.debug(f"Test Task added to calendar: {task_title}: {event_instance.start}")
    else:
        cfg.LOGGER.debug(f"Error adding Test Task to calendar: {task_title}: {event_instance.start}\n{message}")
