"""
Small helper script for configuring a general logger object.
"""
import os
import sys
from loguru import logger


LOG_FORMAT = \
	'<green>{time:YYYY-MM-DD HH:mm:ss}</green> | ' \
	'<level>{level: <7}</level> | ' \
	'<cyan>{name: <28}</cyan> | ' \
	'<cyan>{function: <20}</cyan> | ' \
	'<cyan>{line: >4}</cyan> | ' \
	'{message}'


def set_stdout_logger():
	"""
	Sets and configures a logger for showing in the console.
	:return: None
	"""
	logger.configure(handlers=[{'sink': sys.stderr, 'format': LOG_FORMAT, 'level': 'WARNING'}])

	return


def set_logfile_handler(logfile_name='optimization.log'):
	"""
	Creates a new log file and sets the respective logger handle. Returns the handler's ID.
	:param logfile_name: name of the log file
	:type logfile_name: str
	:return: log file's handler identification
	:rtype: int
	"""
	# Paths
	FILE_PATH = os.path.abspath(os.path.join('logs', logfile_name))

	# Add a new handler, with the same format as the general purpose handler, and return its ID
	handler_id = logger.add(FILE_PATH, format=LOG_FORMAT, rotation="100 MB", backtrace=True, level='DEBUG')

	return handler_id


def remove_logfile_handler(handler_id):
	"""
	Removes a log file's handler from the logger based on its ID.
	:param handler_id: handler's ID
	:type handler_id: int
	:return: None
	"""
	logger.remove(handler_id)

	return
