#!env python3
"""CLI entry point.

CLI handling of piper-whistle commands.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import os
import io
import sys
import pathlib
import argparse
import string
import logging
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch
from .. import piper_whistle


log = logging.getLogger ('tmplr')


class TmplrFile (string.Template):
	delimiter = ':?'


def version ():
	return "0.6.18"


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

	# Subparser for commands.
	subparsers = parser.add_subparsers (dest='command')

	# Setup gues command and options.
	build_readme_args = subparsers.add_parser ('build-readme')
	build_readme_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	build_readme_args.add_argument ('readme_template_path', type=str
		, help='Path to the template used to create the readme.'
		, default=None
	)
	build_readme_args.add_argument ('readme_output_path', type=str
		, help='Path to where output should be placed.'
		, default=None
	)

	# Setup gues command and options.
	build_readme_args = subparsers.add_parser ('build-docs-cfg')
	build_readme_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	build_readme_args.add_argument ('readme_template_path', type=str
		, help='Path to the template used to create the readme.'
		, default=None
	)
	build_readme_args.add_argument ('readme_output_path', type=str
		, help='Path to where output should be placed.'
		, default=None
	)

	return parser


def _run_whistle_main (cmd_args):
	"""! Runs piper-whistle cli and captures stdout as string."""
	cli_output = io.StringIO ()
	with redirect_stdout (cli_output):
		r = piper_whistle.cli.main (cmd_args)

	out_str = cli_output.getvalue ().strip ()
	return out_str


def run_docs_cfg (args):
	"""! Builds readme.md from template file."""
	tmpl_path = pathlib.Path (args.readme_template_path).resolve ()
	if not tmpl_path.exists ():
		log.error (f'Template at "{tmpl_path}" does not exits.')
		return 13

	out_path = pathlib.Path (args.readme_output_path).resolve ()
	if not out_path.parent.exists ():
		log.error (f'Parent path at "{out_path.parent}" does not exits.')
		return 13

	tmpl = None
	with open (tmpl_path.as_posix (), 'r') as f:
		tmpl = TmplrFile (f.read ())

	# Stores template values.
	tmpl_subs = {
		'whistle_version': piper_whistle.version ()
	}

	# Fill template.
	tmpl_str = tmpl.substitute (tmpl_subs)
	with open (out_path.as_posix (), 'w') as f:
		f.write (tmpl_str)
	
	print (f'Template read at "{out_path.as_posix ()}".')

	return 0


def run_build_readme (args):
	"""! Builds readme.md from template file."""
	tmpl_path = pathlib.Path (args.readme_template_path).resolve ()
	if not tmpl_path.exists ():
		log.error (f'Template at "{tmpl_path}" does not exits.')
		return 13

	out_path = pathlib.Path (args.readme_output_path).resolve ()
	if not out_path.parent.exists ():
		log.error (f'Parent path at "{out_path.parent}" does not exits.')
		return 13

	tmpl = None
	with open (tmpl_path.as_posix (), 'r') as f:
		tmpl = TmplrFile (f.read ())

	# Stores help texts.
	tmpl_subs = {}

	# Generate help text for root command.
	tmpl_subs['help_text_root'] = _run_whistle_main (['whistle', '-h'])

	# Generate help messages for sub commands.
	for cmd in piper_whistle.cli.commands:
		cmd_args = ['whistle', cmd, '-h']
		out_str = _run_whistle_main (cmd_args)
		tmpl_var_name = f'help_text_{cmd}'
		tmpl_subs[tmpl_var_name] = out_str

	# Fill template with help texts.
	tmpl_str = tmpl.substitute (tmpl_subs)
	with open (out_path.as_posix (), 'w') as f:
		f.write (tmpl_str)
	
	print (f'Template read at "{out_path.as_posix ()}".')

	return 0


# Build command lookup map.
commands = {
	'build-readme': run_build_readme,
	'build-docs-cfg': run_docs_cfg,
}


def main ():
	"""! Main CLI processing function."""

	# Setup and configure argparse parser.
	parser = create_arg_parser ()
	# Parse passed arguments.
	args = parser.parse_args ()

	# ..
	if args.version:
		print (version ())
		return 0

	# Show help message if no command is provided.
	if None is args.command:
		parser.print_help ()
		return 13

	# Select command and run it.
	if args.command in commands:
		c = commands[args.command]
		log.debug (f'Running {c} with {args} ...')
		r = c (args)
		return r

	# Show available commands.
	parser.print_help ()
	return 13


if '__main__' == __name__:
	r = main ()
	sys.exit (r)
