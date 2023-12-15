"""Logging tool.

Utility functions to help with logging setup.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import logging


default_level = logging.WARNING
default_logger_name = 'holz'
default_logger = logging.getLogger (default_logger_name)
default_format_str = u'[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'
default_formatter = logging.Formatter (default_format_str)
logging.basicConfig (level = default_level, format = default_format_str)


def configure (l, lvl, fmt):
	# Avoid propagation and clear previous stream handlers.
	l.propagate = False
	l.handlers.clear ()

	# Change logger level.
	default_logger.debug (f'Setting {l} to level {lvl}')
	l.setLevel (lvl)

	# Create streaming log channler and set level.
	ch = logging.StreamHandler ()
	ch.setLevel (lvl)
	ch.setFormatter (fmt)
	l.addHandler (ch)

	return l


def setup (log_name, log_level = default_level, log_formatter = default_formatter):
	logger = logging.getLogger (log_name)
	logger = configure (logger
		, log_level
		, log_formatter
	)

	return logger


def setup_default (log_name, log_level = default_level, log_formatter = default_formatter):
	global default_logger_name
	global default_logger
	global default_level
	global default_formatter

	default_logger.info (f'Changing default log to "{log_name}".')

	default_logger_name = log_name
	default_level = log_level
	default_formatter = log_formatter
	default_logger = setup (default_logger_name
		, default_level
		, default_formatter
	)

	return default_logger


def normalize (overrides = {}):
	# collect all logges and normalize their setup / configuration
	loggers = [logging.getLogger ()] \
		+ [logging.getLogger (name) for name in logging.root.manager.loggerDict]

	for l in loggers:
		default_logger.debug (f'Normalizing setup for logger {l} ...')
		if l.name in overrides:
			default_logger.debug (f'Found override for "{l}". Applying ...')
			lvl = overrides[l.name]['level']
			fmttr = default_formatter
			if 'formatter' in overrides[l.name] and not (overrides[l.name]['formatter'] is None):
				fmttr = overrides[l]['formatter']
			configure (l, lvl, fmttr)
		else:
			configure (l, default_level, default_formatter)


def debug (message, category = None):
	logger = None
	if category:
		logger = logging.getLogger (category)
	else:
		logger = default_logger
	logger.debug (message)


def info (message, category = None):
	logger = None
	if category:
		logger = logging.getLogger (category)
	else:
		logger = default_logger
	logger.info (message)


def warn (message, category = None):
	logger = None
	if category:
		logger = logging.getLogger (category)
	else:
		logger = default_logger
	logger.warning (message)


def error (message, category = None):
	logger = None
	if category:
		logger = logging.getLogger (category)
	else:
		logger = default_logger
	logger.error (message)


def fatal (message, category = None):
	logger = None
	if category:
		logger = logging.getLogger (category)
	else:
		logger = default_logger
	logger.fatal (message)
