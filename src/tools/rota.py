#!env python3
"""CLI entry point.

Helps investigating the available versions of packages published on pypi.
Like listing all version names, or get the wheel URL for manual download.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import urllib.request
import urllib.error
import json
import pathlib
import argparse
import logging
import datetime
import time
from ..piper_whistle import holz


def version ():
	return "0.6.18"


def create_arg_parser ():
	"""! Build argparse command line argument parser."""

	# Build top level parser object.
	parser = argparse.ArgumentParser (prog='rota'
		, formatter_class=argparse.RawTextHelpFormatter
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
	refresh_args = subparsers.add_parser ('refresh')
	refresh_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	refresh_args.add_argument ('package_name', type=str
		, help='Name of the package for which index should be refreshed.'
		, default=None
	)

	# Setup gues command and options.
	versions_args = subparsers.add_parser ('versions')
	versions_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	versions_args.add_argument ('package_name', type=str
		, help='Name of the package to list available version for.'
		, default=None
	)

	# Setup gues command and options.
	fotunae_args = subparsers.add_parser ('fortunae')
	fotunae_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	fotunae_args.add_argument ('-n', '--version_name', type=str
		, help='Version string of release to look for.'
		, default=None
	)
	fotunae_args.add_argument ('package_name', type=str
		, help='Name of the package for which to show wheel information.'
		, default=None
	)

	# Setup gues command and options.
	fotunae_args = subparsers.add_parser ('bhavacakra')
	fotunae_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	fotunae_args.add_argument ('script_path', type=str
		, help='Name of the package for which to show wheel information.'
		, default=None
	)

	# Setup gues command and options.
	github_release_args = subparsers.add_parser ('github-release')
	github_release_args.add_argument ('-v', '--verbose'
		, action='store_true'
		, help='Activate verbose logging.'
		, default=False
	)
	github_release_args.add_argument ('-D', '--draft'
		, action='store_true'
		, help='Setup as draft.'
		, default=False
	)
	github_release_args.add_argument ('-P', '--pre-release'
		, action='store_true'
		, help='Tag as pre-release.'
		, default=False
	)
	github_release_args.add_argument ('-T', '--token-file', type = str
		, help = 'Path to the file containig the user token.'
		, default = 'github-release.token'
	)
	github_release_args.add_argument ('-A', '--attachment', type = str
		, help = 'File to attach to release.'
		, default = 'github-release.token'
	)
	github_release_args.add_argument ('repository', type=str
		, help='Repository ID in form of "username/project".'
		, default=None
	)
	github_release_args.add_argument ('branch', type=str
		, help='Branch to lookup commit.'
		, default=None
	)
	github_release_args.add_argument ('tag', type=str
		, help='Version tag.'
		, default=None
	)
	github_release_args.add_argument ('message', type=str
		, help='Message body to associate with release.'
		, default=None
	)

	return parser


def _data_path ():
	user_root_path = pathlib.Path ('~').expanduser ()
	data_path = None
	if user_root_path.joinpath ('.config').exists ():
		data_path = user_root_path.joinpath ('.config', 'rota')
	elif user_root_path.joinpath ('AppData', 'Local').exists ():
		data_path = user_root_path.joinpath ('AppData', 'Local', 'rota')

	return data_path


def run_refresh (args):
	url_root = f'https://pypi.python.org'
	url_path = f'pypi/{args.package_name}/json'
	url = f'{url_root}/{url_path}'

	data_path = _data_path ()
	holz.debug (f'Set data path root to "{data_path}".')
	if not data_path:
		holz.fatal ('Could not determine user path. What OS is this?')
		return 13

	holz.debug (f'Making sure data path exists ...')
	data_path.mkdir (exist_ok=True)

	holz.debug ('Preparing request ...')
	request = urllib.request.Request (url)

	holz.debug ('Reaching out ...')
	opener = urllib.request.urlopen (request)

	if 200 != opener.code:
		holz.error (f'Request finished with {opener.code}.')
		return 13

	holz.debug ('Reading response body ...')
	body = opener.read ()
	if not body or 0 == len (body):
		holz.error (f'Response body empty.')
		return 13

	holz.debug (f'Got {len (body)} bytes.')

	package_info_path = data_path.joinpath (f'{args.package_name}.json')
	holz.debug (f'Writing info to "{package_info_path}" ...')

	data = json.loads (body.decode ('utf-8'))
	raw_data = json.dumps (data, indent=4)
	bw = 0
	with open (package_info_path, 'w+') as f:
		f.seek (0)
		f.truncate ()
		bw = f.write (raw_data)

	holz.debug (f'Info saved, {bw} bytes written.')
	return 0


def run_versions (args):
	data_path = _data_path ()
	holz.debug (f'Set data path root to "{data_path}".')
	if not data_path:
		holz.fatal ('Could not determine user path. What OS is this?')
		return 13

	holz.debug (f'Making sure data path exists ...')
	package_info_path = data_path.joinpath (f'{args.package_name}.json')
	if not package_info_path.exists ():
		holz.error ('No index found. Please refresh.')
		return 13

	j = None
	with open (package_info_path, 'r') as f:
		j = json.load (f)

	try:
		import packaging.version

		versions = [
			packaging.version.parse(v)
			for v in list (j['releases'].keys ())
		]
		sorted_versions = sorted(versions)
		sorted_versions = [str(v) for v in sorted_versions]
		print ('\n'.join (sorted_versions))

		return 0
	except Exception as e:
		holz.debug (str (e))
		holz.debug (
			'Could not import package packaging. Falling back on best guess.'
		)
		pass

	def convert_version_component (component):
		try:
			return int (component)
		except Exception:
			return 999

	def sort_by_component (name):
		return list (map (convert_version_component, name.split ('.')))

	version_names = list (j['releases'].keys ())
	version_names.sort (key = sort_by_component)
	print ("\n".join (version_names))

	return 0


def _parse_timestamp (date_string):
	format_string = '%Y-%m-%dT%H:%M:%S.%fZ'

	parsed = None
	try:
		parsed = datetime.datetime.strptime (date_string, format_string)
		return parsed
	except ValueError as ex:
		holz.debug (str (ex))
		holz.debug ('Failed to parse date. Trying simper format ...')
		format_string = '%Y-%m-%dT%H:%M:%SZ'

	try:
		parsed = datetime.datetime.strptime (date_string, format_string)
	except Exception as ex:
		holz.debug (str (ex))
		holz.error (f'Could not determine datetime format for "{date_string}".')
		return None

	return parsed


def run_fortunae (args):
	data_path = _data_path ()
	holz.debug (f'Set data path root to "{data_path}".')
	if not data_path:
		holz.fatal ('Could not determine user path. What OS is this?')
		return 13

	holz.debug (f'Making sure data path exists ...')
	package_info_path = data_path.joinpath (f'{args.package_name}.json')
	if not package_info_path.exists ():
		holz.error ('No index found. Please refresh.')
		return 13

	j = None
	with open (package_info_path, 'r') as f:
		j = json.load (f)

	if None is args.version_name:
		current = None
		options = j['releases'].keys ()
		prime = None
		for ok in options:
			prime = ok
			break

		for dl in j['releases'][prime]:
			if not dl['url'].endswith ('.whl'):
				current = dl
				break

		if not current:
			holz.error ('No releases yet.')
			return 13

		for relver in options:
			for dl in j['releases'][relver]:
				if not dl['url'].endswith ('.whl'):
					continue
				dl_date = _parse_timestamp (dl['upload_time_iso_8601'])
				cr_date = _parse_timestamp (current['upload_time_iso_8601'])
				if dl_date > cr_date:
					current = dl

		print (current['url'])

		return 0

	if args.version_name not in j['releases']:
		holz.error ('Could not find release with given version.')
		return 13

	holz.info (f'Release files for "{args.version_name}":')
	for r in j['releases'][args.version_name]:
		print (r['url'])

	return 0


def run_bhavacakra (args):
	'''.'''
	import modulefinder

	p = pathlib.Path (args.script_path)
	if not p.exists ():
		holz.error (f'Could not find script at "{args.script_path}".')
		return 13

	finder = modulefinder.ModuleFinder ()
	finder.run_script (args.script_path)
	module_list = finder.modules.items ()

	for name, mod in module_list:
		print('%s: ' % name, end='')
		print(','.join(list(mod.globalnames.keys())[:3]))

	return 0


def _build_create_release_url (username, project):
	gh_root = 'https://api.github.com/repos'
	gh_uname = username
	gh_project = project
	request_url = f'{gh_root}/{gh_uname}/{gh_project}/releases'
	return request_url


def run_github_release (args):
	"""! Creates a new release page

	When set, attaches the file pointed at by --attachment
	"""
	gh_uname = args.repository.split ('/')[0]
	gh_project = args.repository.split ('/')[1]

	tp = pathlib.Path (args.token_file).resolve ()
	if not tp.exists ():
		holz.error (f'Could not find token file at "{tp.as_posix ()}".')
		return 23

	holz.info (f'Reading token from {tp.as_posix ()} ...')
	gh_token = None
	with open (tp, 'r') as f:
		gh_token = f.read ().strip ()

	request_url = _build_create_release_url (gh_uname, gh_project)
	request_headers = {
	}
	request_body = {
		'tag_name': f'{args.tag}',
		'target_commitish': f'{args.branch}',
		'name': f'{gh_project} {args.tag} wheel',
		'body': args.message,
		'draft': bool (args.draft),
		'prerelease': bool (args.pre_release),
		'generate_release_notes': False
	}
	request_data = json.dumps (request_body).encode ('utf-8')

	release_info = None
	try:
		req = urllib.request.Request (request_url
			, data = request_data
		)
		req.add_header ("Accept", "application/vnd.github+json")
		req.add_header ("Authorization", f"Bearer {gh_token}")
		req.add_header ("X-GitHub-Api-Version", "2022-11-28")

		holz.info (f'Creating new release "{request_body["name"]}" ...')
		with urllib.request.urlopen (req) as response:
			release_info = json.loads (response.read ().decode ('utf-8'))
			holz.info (f'New release created at: {release_info["url"]}')
	except urllib.error.HTTPError as ex:
		holz.error (ex)
		holz.error (ex.code)
		holz.error (ex.reason)
		holz.error (ex.headers)
		return 23

	time.sleep (0.66)

	if args.attachment:
		ap = pathlib.Path (args.attachment)
		request_url = release_info['upload_url'].replace (
			'{?name,label}', f'?name={ap.name}'
		)
		request_body = None
		with open (ap, 'rb') as f:
			request_body = f.read ()

		upload_info = None
		try:
			holz.info (f'Uploading "{request_url}" ...')
			req = urllib.request.Request (request_url
				, data = request_data
			)
			req.add_header ("Accept", "application/vnd.github+json")
			req.add_header ("Authorization", f"Bearer {gh_token}")
			req.add_header ("X-GitHub-Api-Version", "2022-11-28")
			req.add_header ("Content-Type", "application/octet-stream")

			holz.info ('Sending attachment ...')
			with urllib.request.urlopen (req) as response:
				upload_info = json.loads (response.read ().decode ('utf-8'))
				holz.info (upload_info)
		except urllib.error.HTTPError as ex:
			holz.error (ex)
			holz.error (ex.code)
			holz.error (ex.reason)
			holz.error (ex.headers)
			return 23

		holz.info (f'Finished with state "{upload_info["state"]}".')
		if 'uploaded' != upload_info["state"]:
			holz.error (f'Attachment not uploaded ({upload_info["state"]}).')
			holz.debug (upload_info)
			return 23

		dl_url = upload_info['browser_download_url']
		holz.info (f'Attachment uploaded. Ready at: {dl_url}')

	return 0


commands = {
	'refresh': run_refresh,
	'versions': run_versions,
	'fortunae': run_fortunae,
	'bhavacakra': run_bhavacakra,
	'github-release': run_github_release
}


def main ():
	# Setup and configure argparse parser.
	parser = create_arg_parser ()
	# Parse passed arguments.
	args = parser.parse_args ()

	# Set appropriate log levels.
	log_level = logging.INFO
	if args.debug:
		log_level = logging.DEBUG

	# Setup and initialize holz logging utility.
	holz.setup_default ('rota'
		, log_level
		, silent=not args.debug
	)
	holz.normalize (silent=not args.debug)

	# Show version number.
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
		holz.debug (f'Running {c} with {args} ...')
		r = c (args)
		return r

	# Show available commands.
	parser.print_help ()
	return 13


if __name__ == '__main__':
	main ()
