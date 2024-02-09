from pathlib import Path
import tzlocal
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Union
from pathlib import Path

from googleapiclient.errors import HttpError

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import configuration as cfg

FMT_DATETIME_CALENDAR= '%Y-%m-%dT%H:%M:%S%z'
FMT_DATETIME_RFC3339 = '%Y-%m-%dT%H:%M:%S.%fZ'

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
            'dateTime': self.start.strftime(FMT_DATETIME_CALENDAR),
            'timeZone': self.start.tzname()
            }

        if self.end:
            self.end = {
            'dateTime': self.end.strftime(FMT_DATETIME_CALENDAR),
            'timeZone': self.end.tzname()
            }

        return asdict(self)

@dataclass
class Task:
    title: str
    due: str #It isn't possible to read or write the time that a task is due via the API.
    kind: Optional[str] = "tasks#task"
    completed: Optional[str] = None
    deleted: Optional[bool] = False
    etag: Optional[str] = None
    hidden: Optional[bool] = False
    id: Optional[str] = None
    links: Optional[List[dict]] = None # You might want to define a separate class for links if their structure is consistent.
    notes: Optional[str] = None
    parent: Optional[str] = None
    position: Optional[str] = None
    selfLink: Optional[str] = None
    status: Optional[str] = 'needsAction'
    updated: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class GoogleService:
    scopes = ['https://www.googleapis.com/auth/tasks.readonly',
            'https://www.googleapis.com/auth/tasks',
            'https://www.googleapis.com/auth/calendar']
    tasks_api = ('tasks', 'v1')
    calendar_api = ('calendar', 'v3')

    def __init__(self, token_path: Path, credentials_path: Path):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.service_tasks = self.initialize_service(self.tasks_api[0], self.tasks_api[1], self.scopes)
        self.service_calendar = self.initialize_service(self.calendar_api[0], self.calendar_api[1], self.scopes)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.service_tasks.close()
        self.service_calendar.close()

    def authenticate(self, credentials_path: Path, scopes:list[str]):
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
        creds = flow.run_local_server(port=0)
        return creds

    def initialize_service(self, api_name:str, api_version:int, scopes:list[str]):
        creds = None

        try:
            creds = Credentials.from_authorized_user_file(str(self.token_path), scopes)
        except Exception as e:
            cfg.LOGGER.error(f'Error loading credentials: {e}')

        if not creds or not creds.valid:
            creds = self.authenticate(self.credentials_path, scopes)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build(api_name, api_version, credentials=creds)

    def get_tasklist(self) -> list[dict]:
        tasklist = self.service_tasks.tasklists().list(maxResults=10).execute()['items'][0]
        return tasklist

    def get_tasks(self, tasklist:dict) -> dict:
        return self.service_tasks.tasks().list(tasklist=tasklist['id']).execute()['items']
    
    def insert_task(self, tasklist:dict, task:Task) -> tuple[bool, str]:
        try:
            self.service_tasks.tasks().insert(tasklist=tasklist['id'], body=task.to_dict()).execute()
            cfg.LOGGER.debug(f"Test Task added to calendar: {task.title}: {task.due}")
            return True, f"Added to calendar: {task.title}: {task.due}"
        except HttpError as err:
            cfg.LOGGER.debug(f"Error adding Test Task to calendar: {task.title}: {task.due}")
            return False, f"Error adding {task.title} to calendar: {err}"

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
            self.service_calendar.events().insert(calendarId='primary', body=event.to_dict()).execute()
            cfg.LOGGER.info(f"Added to calendar: {event.summary}: {event.start} to {event.end}")
            return True, f"Added to calendar: {event.summary}: {event.start} to {event.end}"
        except HttpError as e:
            cfg.LOGGER.error(f"Error adding {event.summary} to calendar: {e}")
            return False, f"Error adding {event.summary} to calendar: {e}"

    def event_exists(self, event: Event):
        # Check if an event with the same details already exists
        existing_events = self.service_calendar.events().list(calendarId='primary').execute().get('items', [])

        for existing_event in existing_events:
            # existing_event_dict = asdict(Event(**existing_event))  # Convert existing event to a dictionary
            if existing_event['status'] != 'cancelled':
                if existing_event['summary'] == event.summary:
                    if datetime.strptime(existing_event['start']['dateTime'], FMT_DATETIME_CALENDAR) == event.start:
                        return True

        return False