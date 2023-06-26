import logging
import os
import traceback

from requests import get

import filesystemutils

log_file_path = os.path.join(filesystemutils.home_directory(True), "botlog.log")
logger = None


def initialize_log_file():
    """
    Removes the log file and creates a new one
    :return:
    """
    global logger, log_file_path

    # Remove log file if it exists
    if filesystemutils.path_exists(log_file_path):
        filesystemutils.remove(log_file_path)

    # Create a logger
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)

    # Create a formatter
    formatter = logging.Formatter('%(levelname)s|%(asctime)s|%(message)s')

    # Create a stream handler for the logger
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # Create a file handler for the logger
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Remove previously existing handlers in logger
    logger.handlers.clear()

    # Add the newly created handlers to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)


# Initialize the log file and its logger
initialize_log_file()


def log(msg):
    global logger

    logger.info(msg)


def log_traceback():
    global logger

    tb = traceback.format_exc()
    logger.error(tb)


def get_public_ip():
    ip = get('https://api.ipify.org').content.decode('utf8')
    return ip
