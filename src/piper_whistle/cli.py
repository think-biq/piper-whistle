"""CLI entry point.

CLI handling of piper-whistle commands.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import sys
import pathlib
import argparse
import logging
# Append root package to path so it can be called with absolute path.
sys.path.append (str (pathlib.Path(__file__).resolve().parents[1]))
# Then import whistle modules via absolute path.
from piper_whistle import holz
from piper_whistle import db
from piper_whistle import cmds
from piper_whistle import version


# Build command lookup map.
commands = {
	'refresh': cmds.run_refresh,
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
	'''.'''
	LOG = logging.getLogger ('whistle-args-exception')

	def __init__ (self
		, status : int
		, message : str
		, help_requested : bool = False
	):
		self.LOG.debug (
			f'Creating new (status: {status}), '
			f'message: "{message}", '
			f'help_requested: {help_requested}'
		)
		super ().__init__ (message)
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
		n = kwargs["prog"] if "prog" in kwargs else "UNNAMED"
		self.LOG.debug (
			f'Setting up "{n}" arg parser.'
		)
		super ().__init__ (*args, **kwargs)
		self._last_error_code = 0
		self._last_error_message = None
		self._help_requested = False

	def print_help (self):
		'''.'''
		self._help_requested = True
		self.LOG.debug (
			'Printing help, then raising WhistleArgsParserException.'
		)
		# Idea based on discussion at:
		# https://stackoverflow.com/a/61039719
		# First print auto-generated help text, then instead of exiting,
		# raise whistle exception so main function can react. It smells like
		# 'exception as flow control' anti-pattern'ish, yet it apperas to me
		# as a reasonable trait-off for this scenario.
		super ().print_help ()
		self.LOG.debug ('Here we go ...')
		raise WhistleArgsParserException (
			self._last_error_code,
			self._last_error_message,
			help_requested=True
		)

	def print_help_raw (self):
		'''.'''
		super ().print_help ()

	def error (self, message: str):
		'''.'''
		self._last_error_message = message
		self._last_error_code = 13
		raise WhistleArgsParserException (
			self._last_error_code,
			self._last_error_message
		)

	def exit (self, status: int = 0, message: str = None):
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
		, help=
			'Refreshes (or sets up) language index '
			'by downloading the latest lookup.'
		, default=False
	)

	# Split object for subparsers.
	subparsers = parser.add_subparsers (dest='command')

	# Setup refresh command and options.
	refresh_args = subparsers.add_parser ('refresh'
		, formatter_class=argparse.RawTextHelpFormatter
		, add_help=False
	)
	refresh_args.add_argument ('-h', '--help'
		, action='help'
		, help='Show help message.'
		, default=False
	)
	refresh_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	refresh_args.add_argument ('-R', '--repository'
		, type=str
		, help=
			'Configures the huggingface repository. '
			'Will be used to build index, and download '
			'all data (e.g. models) from.'
		, default='rhasspy/piper-voices'
	)

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
		, help=
			'Path to channel (named pipe (aka. fifo)) '
			'to which piper is listening.'
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
		, help=
			'Instead of streaming to audio channel, specifies a path to wav'
			' file where speech will be store in.'
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
		# Remember exception.
		parser_ex = ex

	if None is parser_ex:
		holz.debug ('Parsed arguments without exception.')
	elif parser_ex is WhistleArgsParserException:
		# So here we are, exception as flow control. It's just very convenient
		# to be able to identify help requested, since otherwise it seems
		# I'd have to equip every sub-arg-parser with a reference to the main
		# parser and then notify when help was requested in any sub-command. So
		# it comes down to lazyness?! Or economy? Anyway, it seems reasonable.
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
		# Use 'print only function', since overridden
		# print_help raises an exception.
		parser.print_help_raw ()
		return 0

	# Fetch default paths for config and data storage.
	paths = None
	if args.data_root:
		root = pathlib.Path (args.data_root)
		if not root.exists ():
			holz.error (f'Data path not found! ({root.as_posix ()})')
			return 1
		paths = db.data_paths (root.as_posix ())
	else:
		paths = db.data_paths ()

	# Fetch details on where to obtain voice data from.
	repo_info = db.remote_repo_config (paths)

	# Trying to create new context object.
	# Might fail if database is missing / corrupt.
	context = db.context_create (paths, repo_info)
	if not context:
		# Check if refresh is requestsed.
		if args.refresh or 'refresh' == args.command:
			holz.debug ('Refresh requested. Manually constructing context ...')
			context = {
				'paths': paths,
				'db': None,
				'repo': repo_info
			}
		# Otherwise cya.
		else:
			holz.error (
				f'Could not create context. '
				f'Please refresh database using "{sys.argv[0]} refresh"'
			)
			# Use 'print only function', since overridden
			# print_help raises an exception.
			parser.print_help_raw ()
			return 1

	# Show help message if no command is provided.
	if None is args.command:
		if args.refresh:
			# TODO: Deprecate -R in next major update.
			r = commands['refresh'] (context, args)
			return r
		holz.debug ('No command specified.')
		# Use 'print only function', since overridden
		# print_help raises an exception.
		parser.print_help_raw ()
		return 1

	# Select command and run it.
	if args.command in commands:
		holz.debug (f'Running command "{args.command}" ...')
		r = commands[args.command] (context, args)
		holz.debug (f'Finished with "{r}".')
		return r

	holz.error (f'Could not find action binding for command "{args.command}".')

	# Show available commands.
	# Use 'print only function', since overridden
	# print_help raises an exception.
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
