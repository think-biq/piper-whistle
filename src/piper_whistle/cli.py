"""CLI entry point.

CLI handling of piper-whistle commands.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import os
import sys
import argparse
import logging
from . import holz
from . import db
from . import cmds
from . import util
from .__init__ import version


def create_arg_parser ():
	"""! Build argparse command line argument parser."""

	# Build top level parser object.
	parser = argparse.ArgumentParser (
		formatter_class=argparse.RawTextHelpFormatter
	)

	# Setup global flags for verbosity level and version print.
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
	guess_args = subparsers.add_parser ('guess')
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
	selector_args = subparsers.add_parser ('path')
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
	speak_args = subparsers.add_parser ('speak')
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
	list_args = subparsers.add_parser ('list')
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
	list_args.add_argument ('-p', '--install-path'
		, action='store_true'
		, help='List path of voice (if installed).'
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
	preview_args = subparsers.add_parser ('preview')
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
	install_args = subparsers.add_parser ('install')
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
	remove_args = subparsers.add_parser ('remove')
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


def main ():
	"""! Main CLI processing function."""

	# Setup and configure argparse parser.
	parser = create_arg_parser ()
	# Parse passed arguments.
	args = parser.parse_args ()

	log_level = logging.WARNING
	if args.debug:
		log_level = logging.DEBUG
	elif args.verbose:
		log_level = logging.INFO
	# Setup default log level and initialize holz logging utility.
	holz.setup_default ('whistle', log_level)
	holz.normalize ()

	if args.version:
		print (version ())
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
		parser.print_help ()
		return 1

	# Show help message if no command is provided.
	if None is args.command:
		parser.print_help ()
		return 1

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

	# Select command and run it.
	if args.command in commands:
		holz.debug (f'Running command "{args.command}" ...')
		return commands[args.command] (context, args)

	holz.error (f'Could not find command "{args.command}".')

	# Show available commands.
	parser.print_help ()
	return 1


if __name__ == '__main__':
	"""! CLI entry point."""

	r = main ()
	sys.exit (r)
