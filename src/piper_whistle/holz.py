"""Holz logging tool.

Utility functions to help with logging setup.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import logging


default_level = logging.WARNING
default_logger_name = 'holz'
default_logger = logging.getLogger (default_logger_name)
# All options at
# https://docs.python.org/3.8/library/logging.html#logrecord-attributes
default_format_str = u'[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'
default_formatter = logging.Formatter (default_format_str)
default_overrides = {}
default_setup_silent = False
default_flush = False
logging.basicConfig (level = default_level, format = default_format_str)

ALWAYS_FLUSH = False
CURRENT_LOG_OVERRIDES = default_overrides


def configure (lg, lvl, fmt, silent = False):
	'''Recreates output stream and configures given logger.'''
	# Avoid propagation and clear previous stream handlers.
	lg.propagate = False
	lg.handlers.clear ()

	# Change logger level.
	if not silent:
		default_logger.debug (f'Setting {lg} to level {lvl}')
	lg.setLevel (lvl)

	# Create streaming log channler and set level.
	ch = logging.StreamHandler ()
	ch.setLevel (lvl)
	ch.setFormatter (fmt)
	ch.set_name(f'{lg.name}:StreamHandler')
	lg.addHandler (ch)

	return lg


def _handle_logger_config_override (
	overrides, lg, silent = default_setup_silent
):
	'''Utility function to override logger specific configurations.'''
	lvl = overrides[lg.name]['level']
	fmttr = default_formatter
	if (
		('formatter' in overrides[lg.name])
		and
		(not (overrides[lg.name]['formatter'] is None))
	):
		fmttr = overrides[lg]['formatter']
	configure (lg, lvl, fmttr, silent = silent)


def setup (log_name
	, log_level = default_level
	, log_formatter = default_formatter
	, silent = False
):
	'''Create and configure a specific logger.'''
	logger = logging.getLogger (log_name)
	logger = configure (logger
		, log_level
		, log_formatter
		, silent = silent
	)

	return logger


def activate_flush_always (flush):
	'''Indicate holz should flush logging output always.'''
	global ALWAYS_FLUSH
	ALWAYS_FLUSH = flush


def setup_default (log_name
	, log_level = default_level
	, log_formatter = default_formatter
	, log_overrides = {}
	, silent = False
):
	'''Configure holz default values.'''
	global default_logger_name
	global default_logger
	global default_level
	global default_formatter
	global default_overrides
	global default_setup_silent

	if not silent:
		default_logger.debug (f'Changing default log to "{log_name}".')

	default_logger_name = log_name
	default_level = log_level
	default_formatter = log_formatter
	default_overrides = log_overrides
	default_setup_silent = silent
	default_logger = setup (default_logger_name
		, default_level
		, default_formatter
		, default_setup_silent
	)

	return default_logger


def normalize (overrides = {}, silent = default_setup_silent):
	'''Looks for all known logger and normalizes their output and level.'''
	global CURRENT_LOG_OVERRIDES

	if CURRENT_LOG_OVERRIDES != overrides:
		CURRENT_LOG_OVERRIDES = overrides

	# collect all logges and normalize their setup / configuration
	loggers = [logging.getLogger ()] \
		+ [logging.getLogger (name) for name in logging.root.manager.loggerDict]

	for lg in loggers:
		if not silent:
			default_logger.debug (f'Normalizing setup for logger {lg} ...')
		if lg.name in CURRENT_LOG_OVERRIDES:
			if not silent:
				default_logger.debug (f'Found override for "{lg}". Applying ...')
			_handle_logger_config_override (CURRENT_LOG_OVERRIDES
				, lg
				, silent = silent
			)
		else:
			configure (lg, default_level, default_formatter, silent = silent)


def _log (method, message, category, flush = default_flush):
	'''Fetches logger and outputs message with level-specific output.'''
	logger = None
	if category:
		logger = logging.getLogger (category)
	else:
		logger = default_logger
	m = getattr (logger, method)
	m (message)
	if flush or ALWAYS_FLUSH:
		for h in logger.handlers:
			h.flush ()


def debug (message, category = None, flush = False):
	_log ('debug', message, category, flush)


def info (message, category = None, flush = False):
	_log ('info', message, category, flush)


def warn (message, category = None, flush = False):
	_log ('warning', message, category, flush)


def error (message, category = None, flush = False):
	_log ('error', message, category, flush)


def fatal (message, category = None, flush = False):
	_log ('fatal', message, category, flush)


class HolzNotifyLogger(logging.Logger):
	"""
	Logger subclass to notify holz when a new logger is created / requested.
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		global ON_LOGGER_REQUESTED

		if self.name in CURRENT_LOG_OVERRIDES:
			_handle_logger_config_override(CURRENT_LOG_OVERRIDES
				, self
				, default_setup_silent
			)


logging.setLoggerClass(HolzNotifyLogger)
