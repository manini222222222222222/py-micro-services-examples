import os
import sys

from loguru import logger

from app.config.trace_.request_context import get_trace_id

# log path
filepath = os.getenv("LOG_PATH", "../../log")

log_format = (
    "[<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>] "
    "[<level>{level: <8}</level>] "
    "[<yellow>{extra[trace]}</yellow>] "
    "[<magenta>{thread.name}</magenta>] "
    "[<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>] "
    "<level>{message}</level>"
)

# clear built in styles
logger.remove()

# file output configuration
logger.add(
    filepath + "/{time:YYYY-MM-DD}.log", # File name template, {time} placeholder automatically includes date
    rotation="00:00",                    # cut at 00:00 every day
    retention="60 days",                 # log retention for 60 days
    level="INFO",                        # minimum output level
    format=log_format,                   # log format
    encoding="utf-8",                    # prevent chinese garbled characters
    enqueue=True,                        # Asynchronous security (recommended for multiple processes/threads)
    backtrace=True,                      # catch the complete exception chain
    diagnose=True                        # print more detailed traceback
)

# console output configuration
logger.add(
    sys.stdout,
    level="INFO",
    format=log_format,
    enqueue=True,
    backtrace=True,
    diagnose=True
)

# inject trace id
def inject_trace_id(record):
    record["extra"]["trace"] = get_trace_id() or "-"

# inject trace id into the log
log = logger.patch(inject_trace_id)
