- # Logseq to Google Calendar Integration
  
This project provides a Python script for parsing scheduled items from Logseq files and adding them to Google Calendar.  
- ## Features
- Parses Logseq files to extract scheduled items.
- Adds Logseq scheduled items to Google Calendar.
- ## Prerequisites
- Python 3.x
- Required Python packages (install using `pip install -r requirements.txt`):
	- google-auth-oauthlib
	- google-auth-httplib2
	- google-api-python-client
	- tzlocal
- ## Usage
	- **Clone the repository:**
	  ```bash
	  git clone https://github.com/your-username/your-repo.git
	  ```
	- **Install the required dependencies:**
	  ```bash
	  pip install -r requirements.txt
	  ```
	- **Set up Google Calendar API credentials**
		- Follow the instructions in the `google_calendar` folder.
	- **Configure Logseq and Google Calendar paths:**
		- Adjust paths and configurations in `configuration.py`.
	- **Run the main script:**
	  ```bash
	  python main.py
	  ```
	- The script will parse Logseq scheduled items and add them to Google Calendar.
- ## Configuration
	- Adjust the configurations in `configuration.py` to specify paths, API credentials, and other settings.
- ## Recurrence
	- Recurrence will be set in Google Calendar according to the `repeater` field in Logseq
- ## License
	- This project is licensed under the MIT License - see the file for details.
