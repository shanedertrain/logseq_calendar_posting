from itertools import chain
from datetime import datetime

import logseq_handler as lh
import google_calendar as gc
import configuration as cfg

logseq_to_google_calendar_recocurrence_strings = {
    'h': 'HOURLY',
    'd': 'DAILY',
    'w': 'WEEKLY',
    'm': 'MONTHLY',
    'y': 'YEARLY'
}

def format_recurrence_string(recurrence_type, recurrence_period):
    recurrence_rule = f"RRULE:FREQ={recurrence_type}"

    if recurrence_rule is not None and recurrence_period is not None:
        recurrence_rule += f';INTERVAL={recurrence_period}'

    return recurrence_rule

def main():
    logseq_files = lh.return_list_of_markdown_files_in_dir(cfg.LOGSEQ_FOLDER_PATH)
    scheduled_items:list[lh.ScheduledItem] = list(chain.from_iterable(lh.get_scheduled_in_logseq_file(file, exclude_past=True) for file in logseq_files))

    for item in scheduled_items:
        recurrence_rule = None
        if item.recurrence_char is not None:
            recurrence_type = logseq_to_google_calendar_recocurrence_strings.get(item.recurrence_char)
            recurrence_rule = format_recurrence_string(recurrence_type, item.recurrence_period)

        event = gc.Event(summary=item.title, 
                         start=item.scheduled_date,
                         recurrence=[ recurrence_rule ] if recurrence_rule is not None else None,
                         reminders={'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 10}]})

        with gc.GoogleCalendar(token_path=cfg.TOKEN_PATH, credentials_path=cfg.CREDENTIALS_PATH) as CALENDAR:
            success, message = CALENDAR.create_event(event)

        if success:
            cfg.LOGGER.info(f"Event added to Google Calendar: {item.title}: {item.scheduled_date}")
        else:
            if "Not adding duplicate." not in message:
                cfg.LOGGER.error(f"Error adding event to Google Calendar: {item.title}: {item.scheduled_date}\n{message}")
            pass

if __name__ == '__main__':
    main()