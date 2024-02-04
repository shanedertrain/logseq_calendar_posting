from pathlib import Path
import logging

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

ROOT_FOLDER = Path(__file__).parent
OUTPUT_FOLDER = ROOT_FOLDER / 'output'
OUTPUT_FOLDER.mkdir(exist_ok=True)

INPUT_FOLDER = ROOT_FOLDER / 'input'
INPUT_FOLDER.mkdir(exist_ok=True)

LOG_FILEPATH = OUTPUT_FOLDER / 'log.log'

LOGSEQ_FOLDER_PATH = Path("G:\Logseq")
CREDENTIALS_PATH = INPUT_FOLDER / 'credentials.json'
TOKEN_PATH = OUTPUT_FOLDER / 'token.json'

class MStreamHandler(logging.StreamHandler):
  """Handler that controls the writing of the newline character"""

  special_code = '[!n]'

  def emit(self, record) -> None:

    if self.special_code in record.msg:
      record.msg = record.msg.replace( self.special_code, '' )
      self.terminator = '\r'
    else:
      self.terminator = '\n'

    return super().emit(record)

def configure_logger(log_file) -> logging.Logger:
    logger = logging.getLogger('cfg_logger')
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs only messages above INFO level to the file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create stream handler to log messages to the console
    console_handler = MStreamHandler()
    console_handler.setLevel(logging.INFO)  # Change the level as needed

    # Create a formatter and set it to the handler
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s: %(filename)s | %(message)s', '%H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

LOGGER = configure_logger(LOG_FILEPATH)