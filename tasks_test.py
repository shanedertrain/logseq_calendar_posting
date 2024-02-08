from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Union
from pathlib import Path
import tzlocal

from googleapiclient.errors import HttpError

import configuration as cfg
from google_service import GoogleService

FMT_DATETIME = '%Y-%m-%dT%H:%M:%SZ'

from dataclasses import dataclass, field

@dataclass
class Task:
    title: str
    due: str
    # kind: Optional[str] = "tasks#task"
    # completed: Optional[str] = None
    # deleted: Optional[bool] = False
    # etag: Optional[str] = None
    # hidden: Optional[bool] = None
    # id: Optional[str] = None
    # links: Optional[List[dict]] = None # You might want to define a separate class for links if their structure is consistent.
    # notes: Optional[str] = None
    # parent: Optional[str] = None
    # position: Optional[str] = None
    # selfLink: Optional[str] = None
    # status: Optional[str] = 'needsAction'
    # updated: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class GoogleTasks(GoogleService):
    def __init__(self, token_path: Path, credentials_path: Path):
        super().__init__(token_path=token_path, credentials_path=credentials_path)
        self.scopes.extend(['https://www.googleapis.com/auth/tasks.readonly',
                           'https://www.googleapis.com/auth/tasks'])
        self.api['name'] = 'tasks'
        self.api['version'] = 1

    def __enter__(self):
        self.service = self.initialize_service()
        return self

    def get_tasklist(self) -> list[dict]:
        tasklist = self.service.tasklists().list(maxResults=10).execute()['items'][0]
        return tasklist

    def get_tasks(self, tasklist:dict) -> dict:
        return google_tasks.service.tasks().list(tasklist=tasklist['id']).execute()['items']
    
    def insert_task(self, tasklist:dict, task:Task) -> dict:
        return google_tasks.service.tasks().insert(tasklist=tasklist['id'], body=task.to_dict()).execute()


if __name__ == '__main__':
    # Specify the token and credentials paths as Path objects
    custom_token_path = cfg.TOKEN_PATH
    custom_credentials_path = cfg.CREDENTIALS_PATH

    # Create an instance of the GoogleCalendar class with custom paths
    with GoogleTasks(token_path=custom_token_path, credentials_path=custom_credentials_path) as google_tasks:
        try:
            # Call the Tasks API
            tasklist = google_tasks.get_tasklist()
            tasks = google_tasks.get_tasks(tasklist)

            if not tasklist:
                print("No task lists found.")

            print("Task lists:")
            for task in tasks:
                print(f"{task['title']} ({task['id']})")

            task = Task('test', datetime.now().strftime(FMT_DATETIME))

            google_tasks.insert_task(tasklist, task)

        except HttpError as err:
            print(err)
        # task_title = 'Test Task: Complete Assignment'
        # start_datetime = datetime.today()
        
        # Use the create_event method without passing the service explicitly
        # success, message = google_tasks.create_event(event_instance)

        # if success:
        #     cfg.LOGGER.debug(f"Test Task added to calendar: {task_title}: {event_instance.start}")
        # else:
        #     cfg.LOGGER.debug(f"Error adding Test Task to calendar: {task_title}: {event_instance.start}\n{message}")
