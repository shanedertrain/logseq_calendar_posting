from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import configuration as cfg

class GoogleService:
    def __init__(self, token_path: Path, credentials_path: Path):
        self.scopes = []
        self.api = {'name':None, 'version':1}
        self.token_path = token_path
        self.credentials_path = credentials_path
    
    def __enter__(self):
        self.service = self.initialize_service()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.service.close()

    def authenticate(self, credentials_path: Path):
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.scopes)
        creds = flow.run_local_server(port=0)
        return creds

    def initialize_service(self):
        creds = None

        try:
            creds = Credentials.from_authorized_user_file(str(self.token_path), self.scopes)
        except Exception as e:
            cfg.LOGGER.error(f'Error loading credentials: {e}')

        if not creds or not creds.valid:
            creds = self.authenticate(self.credentials_path)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build(self.api['name'], f'v{self.api["version"]}', credentials=creds)