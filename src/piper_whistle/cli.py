"""CLI entry point.

CLI handling of piper-whistle commands.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import os
import sys
import pathlib
import argparse
import logging
# Append root package to path so it can be called with absolute path.
sys.path.append (str (pathlib.Path(__file__).resolve().parents[1]))
# ..
from piper_whistle import holz
from piper_whistle import db
from piper_whistle import cmds
from piper_whistle import util
from piper_whistle import version


# Build command lookup map.
commands = {
	'guess': cmds.run_guess,
	'path': cmds.run_path,
	'speak': cmds.run_speak,
	'list': cmds.run_list,
	'preview': cmds.run_preview,
	'install': cmds.run_install,
	'remove': cmds.run_remove
}
HELP_REQUESTED = False


class WhistleArgsParserException (Exception):
	
	def __init__ (self, status, message, help_requested = False):
		super().__init__ (message)
		self.status = status
		self.help_requested = help_requested

	@property
	def message (self):
		return str (self)


class WhistleArgsParser (argparse.ArgumentParser):
	'''.'''
	LOG = logging.getLogger ('whistle-args')

	def __init__ (self, *args, **kwargs):
		'''.'''
		super ().__init__ (*args, **kwargs)
		self._last_error_code = 0
		self._last_error_message = None
		self._help_requested = False

	def print_help (self):
		'''.'''
		# Idea based on discussion at:
		# https://stackoverflow.com/a/61039719
		super ().print_help ()
		raise WhistleArgsParserException (
			self._last_error_code,
			self._last_error_message,
			help_requested=True
		)

	def print_help_raw (self):
		'''.'''
		super ().print_help ()

	def error (self, message):
		'''.'''
		self._last_error_message = message
		self._last_error_code = 13
		raise WhistleArgsParserException (
			self._last_error_code,
			self._last_error_message
		)

	def exit (self, status=0, message=None):
		'''.'''
		self._last_error_code = status
		self._last_error_message = message

	def has_error (self):
		'''.'''
		return 0 < self._last_error_code

	def last_error (self):
		'''.'''
		return self._last_error_code, self._last_error_message


def create_arg_parser (prog = 'piper_whistle'):
	"""! Build argparse command line argument parser."""

	# Build top level parser object.
	parser = WhistleArgsParser (prog = prog
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)

	# Setup global flags for verbosity level and version print.
	parser.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	parser.add_argument ('-d', '--debug'
		, action='store_true'
		, help='Activate very verbose logging.'
		, default=False
	)
	parser.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	parser.add_argument ('-V', '--version'
		, action='store_true'
		, help='Show version number.'
		, default=False
	)
	parser.add_argument ('-P', '--data-root', type=str
		, help='Root path where whistle should store config and data in.'
		, default=None
	)
	parser.add_argument ('-R', '--refresh'
		, action='store_true'
		, help='Refreshes (or sets up) language index by downloading the latest lookup.'
		, default=False
	)

	# Split object for subparsers.
	subparsers = parser.add_subparsers (dest='command')

	# Setup gues command and options.
	guess_args = subparsers.add_parser ('guess'
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)
	guess_args.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	guess_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	guess_args.add_argument ('language_name', type=str
		, help='A string representing a language name (or code).'
		, default=''
	)

	# Setup path command and options.
	selector_args = subparsers.add_parser ('path'
		, formatter_class=argparse.RawTextHelpFormatter
	)
	selector_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	selector_args.add_argument ('voice_selector', type=str
		, help='Selector of voice to search.'
		, default=''
	)

	# Setup speak command and options.
	speak_args = subparsers.add_parser ('speak'
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)
	speak_args.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	speak_args.add_argument ('something', type=str
		, help='Something to speak.'
		, default=''
	)
	speak_args.add_argument ('-c', '--channel'
		, type=str
		, help='Path to channel (named pipe (aka. fifo)) to which piper is listening.'
		, default='/opt/wind/channels/speak'
	)
	speak_args.add_argument ('-j', '--json'
		, action='store_true'
		, help='Encode the text as json payload. Is on by default.'
		, default=True
	)
	speak_args.add_argument ('-r', '--raw'
		, action='store_true'
		, help='Encode the text directly.'
		, default=False
	)	
	speak_args.add_argument ('-o', '--output'
		, type=str
		, help='Instead of streaming to audio channel, specifies a path to wav file where speech will be store in.'
		, default=None
	)
	speak_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)

	# Setup list command and options.
	list_args = subparsers.add_parser ('list'
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)
	list_args.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	list_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	list_args.add_argument ('-I', '--installed'
		, action='store_true'
		, help='Only list installed voices.'
		, default=False
	)
	list_args.add_argument ('-a', '--all'
		, action='store_true'
		, help='List voices for all available languages.'
		, default=False
	)
	list_args.add_argument ('-L', '--languages'
		, action='store_true'
		, help='List available languages.'
		, default=False
	)
	list_args.add_argument ('-g', '--legal'
		, action='store_true'
		, help='Show avaiable legal information.'
		, default=False
	)
	list_args.add_argument ('-U', '--show-url'
		, action='store_true'
		, help='Show URL of voice on remote host.'
		, default=False
	)
	list_args.add_argument ('-S', '--omit-speakers'
		, action='store_true'
		, help='Omit speakers form listing.'
		, default=False
	)
	list_args.add_argument ('-p', '--install-path'
		, action='store_true'
		, help='Show path of voice (if installed).'
		, default=False
	)
	list_args.add_argument ('-l', '--language-code'
		, type=str
		, help='Only list voices matching this language.'
		, default='en_GB'
	)
	list_args.add_argument ('-i', '--voice-index'
		, type=int
		, help='List only specific language voice.'
		, default=-1
	)

	# Setup preview command and options.
	preview_args = subparsers.add_parser ('preview'
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)
	preview_args.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	preview_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	preview_args.add_argument ('-l', '--language-code'
		, type=str
		, help='Select language.'
		, default='en_GB'
	)
	preview_args.add_argument ('-i', '--voice-index'
		, type=int
		, help='Specific language voice. (defaults to first one)'
		, default=0
	)
	preview_args.add_argument ('-s', '--speaker-index'
		, type=int
		, help='Specific language voice speaker. (defaults to first one)'
		, default=0
	)
	preview_args.add_argument ('-D', '--dry-run'
		, action='store_true'
		, help='Build URL and simulate download.'
		, default=False
	)
	
	# Setup install command and options.
	install_args = subparsers.add_parser ('install'
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)
	install_args.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	install_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	install_args.add_argument ('-D', '--dry-run'
		, action='store_true'
		, help='Simulate download / install.'
		, default=False
	)
	install_args.add_argument ('language_code'
		, type=str
		, help='Select language.'
	)
	install_args.add_argument ('voice_index'
		, type=int
		, help='Specific language voice. (defaults to first one)'
	)

	# Setup remove command and options.
	remove_args = subparsers.add_parser ('remove'
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)
	remove_args.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	remove_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	remove_args.add_argument ('voice_selector', type=str
		, help='Selector of voice to search.'
		, default=''
	)

	return parser


def main (custom_args, force_debug = False):
	"""! Main CLI processing function."""
	log_level = logging.WARNING

	# Setup and configure argparse parser.
	parser_ex = None
	parser = create_arg_parser ()
	try:
		# Parse passed arguments.
		args = parser.parse_args (args = custom_args[1:])
	except Exception as ex:
		# Setup holz just before handling exception.
		if force_debug:
			log_level = logging.DEBUG
		holz.setup_default ('whistle', log_level)
		holz.normalize ()
		parser_ex = ex

	if None is parser_ex:
		holz.debug ('Parsed arguments without exception.')
	elif type (parser_ex) == WhistleArgsParserException:
		if parser_ex.help_requested:
			holz.debug ('Parser help was requested.')
			# Since message has already been put to stdout, we can exit.
			return 0

		# Notify about exception.
		holz.error (parser_ex.message)

		# Return forwarded status code.
		return parser_ex.status
	else:
		holz.fatal (f'Unexpected error: {parser_ex}')
		return 23


	# Determine log level for holz setup.
	if args.debug or force_debug:
		log_level = logging.DEBUG
	elif args.verbose:
		log_level = logging.INFO

	# Setup default log level and initialize holz logging utility.
	holz.setup_default ('whistle', log_level)
	holz.activate_flush_always (True)
	holz.normalize ()
	holz.debug ('Holz setup done and available loggers normalized.')

	if args.version:
		print (version.as_string ())
		return 0

	if args.help:
		parser.print_help_raw ()
		return 0

	# Fetch default paths for config and data storage.
	paths = None
	if args.data_root:
		if not os.path.exists (args.data_root):
			holz.error (f'Data path not found! ({args.data_root})')
			return 1
		paths = db.data_paths (args.data_root)
	else:
		paths = db.data_paths ()

	# Fetch details on where to obtain voice data from.
	repo_info = db.remote_repo_config ()
	
	# Check if refresh is requestsed.
	if args.refresh:
		holz.info ('Fetching and rebuilding database ...')
		context = db.index_download_and_rebuild (paths, repo_info)
		with open (context['paths']['last-updated'], 'r') as f:
			sys.stdout.write (f.read ())
		return 0

	# Trying to create new context object. Might fail if database is missing / corrupt.
	context = db.context_create (paths, repo_info)
	if not context:
		holz.error (
			f'Could not create context. ' \
			f'Please refresh database using "{sys.argv[0]} -vR"'
		)
		parser.print_help_raw ()
		return 1

	# Show help message if no command is provided.
	if None is args.command:
		parser.print_help_raw ()
		return 1

	# Select command and run it.
	if args.command in commands:
		holz.debug (f'Running command "{args.command}" ...')
		r = commands[args.command] (context, args)
		holz.debug (f'Finished with "{r}".')
		return r

	holz.error (f'Could not find command "{args.command}".')

	# Show available commands.
	parser.print_help_raw ()
	return 1


def main_sys ():
	"""! CLI entry point with sys.argv as default parameters."""
	# Call CLI entry function.
	r = main (sys.argv)
	# Exit with return code.
	sys.exit (r)


if __name__ == '__main__':
	"""! CLI entry point."""
	main_sys ()
