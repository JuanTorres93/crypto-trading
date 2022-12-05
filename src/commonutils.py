import logging
import os
import traceback

import filesystemutils

log_file_path = os.path.join(filesystemutils.home_directory(True), "botlog.log")

if filesystemutils.path_exists(log_file_path):
    filesystemutils.remove(log_file_path)

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s|%(asctime)s|%(message)s',
                    handlers=[
                        logging.FileHandler(log_file_path),
                        logging.StreamHandler()
                    ])


def log(msg):
    logging.info(msg)


def log_traceback():
    tb = traceback.format_exc()
    logging.error(tb)

