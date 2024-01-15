"""CLI functions corresponding to available commands.

Defines functions to handle available CLI commands.
```
guess: run_guess
path: run_path
speak: run_speak
list: run_list
preview: run_preview
install: run_install
remove: run_remove
```
Command handle function get passed whistle context and argparse arguments.

"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import subprocess
import sys
import json
import pathlib
# Append root package to path so it can be called with absolute path.
sys.path.append (str (pathlib.Path(__file__).resolve().parents[1]))
from piper_whistle import holz
from piper_whistle import db
from piper_whistle import util


def _run_program (params):
	"""! Runs external program with given parameters
	@param params List of parameters to use for program invokation.
	@return Returns a touple containing (returncode, stdout, stderr)
	"""
	holz.debug (f'Running external program: {params}')
	p = subprocess.Popen (params
		, bufsize=0
		, stdout=subprocess.PIPE
		, stderr=subprocess.PIPE
	)

	out, err = p.communicate ()
	holz.debug (f'Exit with {p.returncode}')
	return (p.returncode, out, err)


def _parse_voice_selector (selector):
	"""! Get voice details from selector string.
	@param selector Voice identifying string.
	@return Returns a touple containgin (name, quality, speaker) of the voice.
	"""
	if '-' in selector:
		code, name, quality = selector.split ('-')
		return name, quality, 0

	name, rest = selector.split ('@')
	if '/' in rest:
		quality, speaker = rest.split ('/')
	else:
		quality = rest
		speaker = 0

	return name, quality, speaker


def run_refresh (context, args):
	"""! Run command 'refresh'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	if 'refresh' == args.command:
		context['repo']['repo-id'] = args.repository
	else:
		holz.warn (
			f'-R will be phased out within the next couple releases. '
			f'Please use the "refresh" command.'
		)

	holz.info (
		f'Fetching and rebuilding database '
		f'from "{context["repo"]["repo-id"]}" ...'
	)
	context = db.index_download_and_rebuild (context['paths'], context['repo'])
	if not context:
		holz.info (f'Could not rebuild index.')
		return 13

	holz.debug (
		f"Noting last update time to '{context['paths']['last-updated']}'."
	)
	with open (context['paths']['last-updated'], 'r') as f:
		sys.stdout.write (f.read ())

	return 0


def run_guess (context, args):
	"""! Run command 'guess'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	target_lang = args.language_name
	matching_code = db.context_guess_language_from_name (context, target_lang)

	if matching_code:
		lang = context['db']['languages'][matching_code]
		holz.info (
			f'Best guess for "{target_lang}": '
			f'{matching_code} ({lang["name_native"]} [{lang["name_english"]}])'
		)
		sys.stdout.write (matching_code)
		return 0

	holz.error (f'Could not find anything matching: {target_lang}')
	return 13


def run_path (context, args):
	"""! Run command 'path'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	selector = args.voice_selector

	code = None
	if ':' in selector:
		code, selector = selector.split (':')

	name, quality, speaker = _parse_voice_selector (selector)

	model_info = {
		'name': name,
		'quality': quality,
		'speaker': speaker
	}
	voice_file_path = db.model_resolve_path (context['paths'], model_info)
	if not voice_file_path:
		holz.error (f'Could not find any voice matching {name}!')
		return 13

	sys.stdout.write (voice_file_path)
	return 0


def run_speak (context, args):
	"""! Run command 'speak'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	p = pathlib.Path (args.channel)

	if not p.exists ():
		holz.error (f'No channel at "{p}" found.')
		return 13

	with open (p, 'w') as f:
		payload = f'{args.something}'
		if args.json:
			j = {'text': payload}
			if args.output:
				# If relative path, prepend current working directory.
				op = pathlib.Path (args.output)
				if not op.is_absolute ():
					op = pathlib.Path.cwd ().joinpath (args.output)
				j['output_file'] = op.absolute ().as_posix ()
			payload = json.dumps (j)

		payload = payload + '\n'

		holz.info (f'Sending {len (payload)} bytes ...')
		r = f.write (payload)
		holz.info (f'{r} bytes sent.')

	return 0


def run_list (context, args):
	"""! Run command 'list'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	langdb = context['db']['languages']

	if args.languages:
		available_lang_codes = '\n'.join ([c for c in langdb])
		sys.stdout.write (f'{available_lang_codes}')
		return 0

	if args.installed:
		voice_i = 0
		for model in db.model_list_installed (context['paths']):
			code = model['code']
			sys.stdout.write (
				f"\t{code}:{model['name']}@{model['quality']}"
			)
			if args.verbose:
				sys.stdout.write (f"\t{model['path']}")
			if args.legal:
				lgl = context['db']['legal'][model['name']]
				a = f"Voice[{lgl['training']}]: {lgl['license']}, " \
					f"Reference: {lgl['reference']}, " \
					f"Dataset: {lgl['dataset-url']}"
				sys.stdout.write (f"\t{a}")
			if args.show_url:
				download_info = db.assemble_download_info (context
					, code
					, voice_i
				)
				sys.stdout.write (f"\t{download_info['model']['url']}")
			sys.stdout.write ("\n")
			voice_i += 1

		return 0

	if args.all:
		for code in langdb:
			lang = langdb[code]

			sys.stdout.write (f'Voices for "{code}":\n')
			voice_i = 0
			for voice_name in lang['voices']:
				details = voice_name
				if args.legal:
					lgl = context['db']['legal'][voice_name]
					a = f"Voice[{lgl['training']}]: {lgl['license']}, " \
						f"Reference: {lgl['reference']}, " \
						f"Dataset: {lgl['dataset-url']}"
					details = f"{details}\t({a})"
				if args.show_url:
					download_info = db.assemble_download_info (context
						, code
						, voice_i
					)
					details = f"{a}\t{download_info['model']['url']}"
				sys.stdout.write (f"\t{voice_i}: {details}\n")

				voice_i = voice_i + 1

		return 0

	code = args.language_code
	if code not in langdb:
		holz.error (f'Could not find language with code "{code}".')
		return 13

	lang = langdb[code]
	voice_i = args.voice_index
	index = context['db']['index']

	if -1 < voice_i:
		voice_name = lang['voices'][voice_i]

		sys.stdout.write (f'{voice_name}\t{voice_i}')
		if args.legal:
			lgl = context['db']['legal'][voice_name]
			a = f"Voice[{lgl['training']}]: {lgl['license']}, "\
				f"Reference: {lgl['reference']}, " \
				f"Dataset: {lgl['dataset-url']}"
			sys.stdout.write (f'\t{a}')
		if args.show_url:
			download_info = db.assemble_download_info (context
				, code
				, voice_i
			)
			sys.stdout.write (f"\t{download_info['model']['url']}")

		sys.stdout.write ('\n')

		if not args.omit_speakers:
			speakers = index[voice_name]['speaker_id_map']

			sys.stdout.write (f'Speakers:\n')
			if 0 == len (speakers):
				sys.stdout.write (f'\t\t0 (no-name)')
			else:
				for speaker_id in speakers:
					sys.stdout.write (f'\t\t{speakers[speaker_id]:3} ({speaker_id})')
	else:
		sys.stdout.write (f'Available voices ({code}):\n')
		voice_i = 0
		for voice_name in lang['voices']:
			sys.stdout.write (f"\t{voice_i}: {voice_name}")
			if args.legal:
				lgl = context['db']['legal'][voice_name]
				a = f"Voice[{lgl['training']}]: {lgl['license']}, " \
					f"Reference: {lgl['reference']}, " \
					f"Dataset: {lgl['dataset-url']}"
				sys.stdout.write (f'\t{a}')
			if args.show_url:
				download_info = db.assemble_download_info (context
					, code
					, voice_i
				)
				sys.stdout.write (f"\t{download_info['model']['url']}")
			sys.stdout.write ('\n')

			voice_i += 1

	return 0


def run_preview (context, args):
	"""! Run command 'preview'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	dry_run = args.dry_run
	code = args.language_code
	voice_i = args.voice_index
	speaker_i = args.speaker_index

	holz.info (f'Looking up preview info for {code}:{voice_i}:{speaker_i} ...')
	speaker_url = None
	download_info = db.assemble_download_info (context, code, voice_i)
	if download_info:
		if -1 < speaker_i and speaker_i < len (download_info['samples']):
			speaker_url = download_info['samples'][speaker_i]

	holz.debug (download_info)

	if not speaker_url:
		holz.error ('Could not find sample for this voice.')
		return 13

	# Construct path where preview sample are held.
	p = pathlib.Path (f"{context['paths']['voices']}")
	p = p.joinpath (f"{download_info['local_path_relative']}")
	p = p.joinpath (f"samples")
	p = p.resolve ()
	holz.debug (f'Processing preview in path "{p}" ...')

	# Make sure path exists.
	p.mkdir (parents=True, exist_ok=True)

	filename = util.url_path_split (speaker_url)[-1]
	file_path = p.joinpath (filename)
	if file_path.exists ():
		holz.info ('Cached file detected.')
	else:
		holz.info (f'Downloading ({speaker_url}) ...')
		if dry_run:
			sys.stdout.write (f'dl {speaker_url} > {file_path.as_posix ()}\n')
		else:
			r = util.download_as_stream_with_progress (
				speaker_url, file_path.as_posix ()
			)
			if 0 > r:
				holz.error ('Error downloading model.')
				return 13

	sys.stderr.write (f'Playing {file_path.as_posix ()} ...\n')
	if dry_run:
		sys.stdout.write (f'Dry-run, skipping play.')
	else:
		if not file_path.exists ():
			holz.error ('File not found.')
			return 13

		# Suppress playsound's warning message about pygobject.
		# Has to be done before loading modulde, since the loading code
		# is producing the log message.
		import logging
		holz.setup ('playsound', logging.ERROR)

		# After setup, load the module and play the sound.
		from playsound import playsound
		# TODO: On linux, this spins up another python instance, which is
		# not the most convenient way in terms of stopping / cancelling.
		playsound (file_path.as_posix (), block = True)

		holz.info (f'Finished with: 0')

	return 0


def run_install (context, args):
	"""! Run command 'install'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	dry_run = args.dry_run
	code = args.language_code
	voice_i = args.voice_index

	download_info = db.assemble_download_info (context, code, voice_i)
	if not download_info:
		holz.error ('Could not find any downloads for this configuration.')
		return 13

	p = pathlib.Path (f"{context['paths']['voices']}")
	p = p.joinpath (f"{download_info['local_path_relative']}")
	p = p.resolve ()

	p.mkdir (parents=True, exist_ok=True)
	holz.info (f'Using voice path at: {p}')

	config_url = download_info['config']['url']
	config_filename = util.url_path_split (config_url)[-1]
	config_file_path = p.joinpath (config_filename)
	if not config_file_path.exists ():
		size = util.float_round (float (download_info['config']['size']) / 1024)
		holz.info (f'Fetching config ({size}kb) ...')
		if not dry_run:
			r = util.download_as_stream_with_progress (config_url
				, config_file_path.as_posix ()
			)
			if 0 > r:
				holz.error ('Error downloading config.')
				return 13

	else:
		holz.info ('Config already cached.')

	model_url = download_info['model']['url']
	model_filename = util.url_path_split (model_url)[-1]
	model_name = model_filename.split ('.')[0]
	model_file_path = p.joinpath (model_filename)
	if not model_file_path.exists ():
		size = util.float_round (
			float (download_info['model']['size'])
			/ 1024
			/ 1024
		)
		holz.info (f'Fetching {model_name} ({size}mb) ...')
		if not dry_run:
			r = util.download_as_stream_with_progress (
				model_url, model_file_path.as_posix ()
			)
			if 0 > r:
				holz.error ('Error downloading model.')
				return 13
	else:
		holz.info ('Model already cached.')

	selector = download_info["selection_name"]
	sys.stdout.write (f'{selector}\t{model_name}\t{model_file_path}')

	return 0


def run_remove (context, args):
	"""! Run command 'remove'
	@param context Context information and whistle database.
	@param args Processed arguments (prepared by argparse).
	@return Returns 0 on success, otherwise > 0.
	"""
	selector = args.voice_selector

	code = None
	if ':' in selector:
		code, selector = selector.split (':')

	name, quality, speaker = _parse_voice_selector (selector)

	model_info = {
		'name': name,
		'quality': quality,
		'speaker': speaker
	}
	did_remove = db.model_remove (context['paths'], model_info)
	if not did_remove:
		holz.error (f'Could not remove "{name}@{quality}"!')
		return 13

	return 0
