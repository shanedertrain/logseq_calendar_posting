from itertools import chain
import logseq_handler as lh
import google_service as gs
import configuration as cfg

logseq_to_google_calendar_recocurrence_strings = {
    'h': 'HOURLY',
    'd': 'DAILY',
    'w': 'WEEKLY',
    'm': 'MONTHLY',
    'y': 'YEARLY'
}

EVENT = 'EVENT'
TASK = 'TASK'

def format_recurrence_string(recurrence_type, recurrence_period):
    recurrence_rule = f"RRULE:FREQ={recurrence_type}"

    if recurrence_rule is not None and recurrence_period is not None:
        recurrence_rule += f';INTERVAL={recurrence_period}'

    return recurrence_rule

def main():
    logseq_files = lh.return_list_of_markdown_files_in_dir(cfg.LOGSEQ_FOLDER_PATH)
    scheduled_items:list[lh.ScheduledItem] = list(chain.from_iterable(lh.get_scheduled_in_logseq_file(file, exclude_past=True) for file in logseq_files))

    with gs.GoogleService(token_path=cfg.TOKEN_PATH, credentials_path=cfg.CREDENTIALS_PATH) as SERVICE:
        for item in scheduled_items:
            recurrence_rule = None

            if item.recurrence_char is not None:
                recurrence_type = logseq_to_google_calendar_recocurrence_strings.get(item.recurrence_char)
                recurrence_rule = format_recurrence_string(recurrence_type, item.recurrence_period)

            event_type = EVENT if item.has_time == True else TASK
            
            if event_type in [EVENT]:
                event = gs.Event(summary=item.title, 
                            start=item.scheduled_date,
                            recurrence=[ recurrence_rule ] if recurrence_rule is not None else None,
                            reminders={'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 10}]})
                success, message = SERVICE.create_event(event)
            elif event_type in [TASK]:
                task = gs.Task(title=item.title,
                            due=item.scheduled_date.strftime(gs.FMT_DATETIME_RFC3339))
                tasklist = SERVICE.get_tasklist()

                tasks_in_tasklist = SERVICE.get_tasks(tasklist)
                if task.title not in [item['title'] for item in tasks_in_tasklist]:
                    success, message = SERVICE.insert_task(tasklist, task)
                else:
                    cfg.LOGGER.debug(f"Task already exists in calendar: {item.title}")
                

if __name__ == '__main__':
    main()