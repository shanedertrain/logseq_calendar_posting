from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog as fd

import configuration as cfg

recurrence_chars = ['++', '.+']

@dataclass
class ScheduledItem:
    title: str
    scheduled_date: datetime
    has_time: bool
    recurrence_char: str = None
    recurrence_period: int = None

def get_scheduled_in_logseq_file(file_path:Path, exclude_past = False) -> ScheduledItem:
    remove_prefixes = ['TODO ', 'DONE ', 'LATER ']
    scheduled_items = []

    with open(file_path, 'r') as file:
        #avoiding iterating over lines of all files
        if 'SCHEDULED:' in file.read():
            file.seek(0) #reset file pointer after checking for scheduled string
            lines = file.readlines()

            for i, line in enumerate(lines):
                if 'SCHEDULED:' in line:
                    recurrence_period = None
                    recurrence_char = None

                    scheduled_date_str = line.split('<', 1)[1].split('>', 1)[0]
                    title = lines[i-1].strip().lstrip('- ')
    
                    for prefix in remove_prefixes:
                        title = title.replace(prefix, '')

                    title = title.split(" #", 1)[0]

                    #extract reocurrence
                    for char in recurrence_chars:
                        if char in line:
                            scheduled_date_str = scheduled_date_str.split(char)[0].strip()
                            recurrence_str = line.split(char, 1)[-1].split(">")[0] #4w
                            recurrence_period = recurrence_str[0] #4
                            recurrence_char = recurrence_str[1] #w

                    try:
                        scheduled_date = datetime.strptime(scheduled_date_str, "%Y-%m-%d %a %H%M")
                    except ValueError:
                        try:
                            scheduled_date = datetime.strptime(scheduled_date_str, "%Y-%m-%d %a %H:%M")
                        except ValueError:
                            scheduled_date = datetime.strptime(scheduled_date_str, "%Y-%m-%d %a")

                    has_time = scheduled_date.time() != datetime.min.time()

                    if exclude_past and scheduled_date < datetime.now()-timedelta(days=2):
                        continue

                    scheduled_items.append(ScheduledItem(title=title, 
                                                        scheduled_date=scheduled_date, 
                                                        has_time=has_time,
                                                        recurrence_char=recurrence_char,
                                                        recurrence_period=recurrence_period))
    return scheduled_items

def parse_recurrence(recurrence_str):
    unit_mapping = {'h': 'hours', 'd': 'days', 'w': 'weeks', 'm': 'months', 'y': 'years'}

    try:
        amount = int(recurrence_str[:-1])
        unit = unit_mapping.get(recurrence_str[-1])
        return timedelta(**{unit: amount})
    except (ValueError, TypeError, KeyError):
        return timedelta()

def return_list_of_markdown_files_in_dir(directory_path):
    logseq_files = []
    directory = Path(directory_path)

    for file_path in directory.rglob('*.md'):
        # Ignore folders with the title 'logseq'
        if 'logseq' not in file_path.parts:
            logseq_files.append(file_path)

    return logseq_files

if __name__ == '__main__':
    # For debugging purposes, set the default directory
    selected_directory = cfg.LOGSEQ_FOLDER_PATH#fd.askdirectory()

    logseq_files = return_list_of_markdown_files_in_dir(selected_directory)

    scheduled_items = []

    for logseq_file in logseq_files:
        print(f"Parsing Logseq file: {logseq_file}")
        scheduled_items.extend(get_scheduled_in_logseq_file(logseq_file))

    for item in scheduled_items:
        print(item.title)
