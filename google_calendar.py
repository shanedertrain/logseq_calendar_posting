from datetime import datetime, timezone
import tzlocal
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import configuration as cfg

SCOPES = ['https://www.googleapis.com/auth/calendar']

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

    def create_event(self, summary, start_time: datetime, end_time: datetime = None, recurrence_rule=None):
        event_type = 'event'
        
        # Get the local time zone dynamically
        local_timezone = tzlocal.get_localzone()

        # Ensure start time is in the correct format for Google Calendar
        start_time = start_time.replace(tzinfo=local_timezone)

        # If end_time is not provided, set it to be the same as the start time
        if end_time is None:
            end_time = start_time
        else:
            end_time = end_time.replace(tzinfo=local_timezone)

        # Check if the event already exists
        if self.event_exists(summary, start_time, end_time):
            # cfg.LOGGER.info(f"Event with summary '{summary}' already exists. Not adding duplicate.")
            return False, f"Event with summary '{summary}' already exists. Not adding duplicate."

         # Create the event with time zone information
        event = {
            'summary': summary,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': local_timezone.key},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': local_timezone.key},
        }

        # Add recurrence rule if provided
        if recurrence_rule: #recurrence_rule = 'RRULE:FREQ=DAILY'
            event['recurrence'] = [recurrence_rule]

        if start_time.date() == end_time.date():
            event_type = 'Task'
        else:
            event_type = "Event"

        # Add the event to the calendar
        try:
            self.service.events().insert(calendarId='primary', body=event).execute()
            # cfg.LOGGER.info(f"{event_type} added to calendar: {summary}: {start_time} {f'to {end_time}' if event_type != 'Task' else ''}")
            return True, f"{event_type} added to calendar: {summary}: {start_time} {f'to {end_time}' if event_type != 'Task' else ''}"
        except HttpError as e:
            # cfg.LOGGER.error(f"Error adding {event_type} to calendar: {e}")
            return False, f"Error adding {event_type} to calendar: {e}"

    def event_exists(self, summary, start_time, end_time):
        # Check if an event with the same summary, start time, and end time already exists
        events = self.service.events().list(calendarId='primary').execute().get('items', [])

        for event in events:
            existing_summary = event.get('summary', '')
            existing_start_time = event.get('start', {}).get('dateTime', '')
            existing_end_time = event.get('end', {}).get('dateTime', '')

            if (
                existing_summary == summary
                and existing_start_time == start_time.isoformat()
                and existing_end_time == end_time.isoformat()
            ):
                return True

        return False

if __name__ == '__main__':
    # Specify the token and credentials paths as Path objects
    custom_token_path = cfg.TOKEN_PATH
    custom_credentials_path = cfg.CREDENTIALS_PATH

    # Create an instance of the GoogleCalendar class with custom paths
    google_calendar = GoogleCalendar(token_path=custom_token_path, credentials_path=custom_credentials_path)

    # Example: Add a task to the calendar using a datetime object
    task_title = 'Test Task: Complete Assignment'
    task_datetime = datetime(2024, 2, 4, 10, 0, 0)

    # Use the create_event method without passing the service explicitly
    success, message = google_calendar.create_event(task_title, task_datetime)

    if success:
        print(f"Test Task added to calendar: {task_title}: {task_datetime}")
    else:
        print(f"Error adding Test Task to calendar: {task_title}: {task_datetime}\n{message}")
