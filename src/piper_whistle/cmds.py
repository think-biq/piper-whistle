"""CLI functions corresponding to available commands.

Defines functions to handle available CLI commands.
```
guess: run_guess
path: run_path
speak: run_speak
list: run_list
preview: run_preview
install: run_instal
```
Command handle function get passed whistle context and argparse arguments.

"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import subprocess
import os
import sys
import json
import requests
import userpaths
import time
import urllib
import pathlib
from . import holz
from . import db
from . import util


def _run_program (params):
	"""! Runs external program with given parameters
	@param params List of parameters to use for program invokation.
	@return Returns a touple containing (returncode, stdout, stderr)
	"""
	holz.debug (f'Running external program: {params}')
	p = subprocess.Popen (params
		, bufsize=0
		, stdout=subprocess.PIPE
		,  stderr=subprocess.PIPE
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


def _assemble_download_info (context, code, voice_i):
	"""! Compile details used to download voice data.

	The assembled information may look like this:
	{
		'langugage': en_GB,
		'model': {
			'url': "https://...",
			'size': 777,
			'md5': some md5 hash
		},
		'config': {
			'url': "https://...",
			'size': 777,
			'md5': some md5 hash
		},
		'samples': [
			list of URLs to a sample voice reading for each speaker
		],
		'local_path_relative': /some/local/path,
		'selection_name': selector name,
	}	

	@param context Context information and whistle database.
	@param code Language code of voice to be downloaded.
	@param voice_i Voice index to be downloaded.
	@return Returns a map containing download information.
	"""
	index = context['db']['index']
	langdb = context['db']['languages']
	# For example: "https://huggingface.co/rhasspy/piper-voices/resolve/main"
	base_url = db.remote_repo_build_branch_root (context['repo'])

	# Check if given code is available and collect meta info for later
	# download and storage.
	if code in langdb:
		lang = langdb[code]
		voices = lang["voices"]
		# Select specific voice by index.
		if -1 < voice_i and voice_i < len (voices):
			voice_name = voices[voice_i]
			holz.info (f'Requesting "{voice_name}" ...')
			voice_details = index[voice_name]
			
			download_info = {
				'langugage': code,
				'model': None,
				'config': None,
				'samples': [],
				'local_path_relative': f'{code}/{voice_name}',
				'selection_name': f"{code}:{voice_details['name']}@{voice_details['quality']}"
			}

			# Identify onnx speech model files.
			for file in voice_details['files']:
				if file.endswith ('.onnx'):
					download_info['model'] = {
						'url': f'{base_url}/{file}',
						'size': voice_details['files'][file]['size_bytes'],
						'md5': voice_details['files'][file]['md5_digest']
					}
				elif file.endswith ('.onnx.json'):
					download_info['config'] = {
						'url': f'{base_url}/{file}',
						'size': voice_details['files'][file]['size_bytes'],
						'md5': voice_details['files'][file]['md5_digest']
					}

			voice_base_url = os.path.dirname (download_info['model']['url'])

			def build_sample_url (base, speaker_name, speaker_id, ext = 'mp3'):
				return f'{base}/samples/{speaker_name}_{speaker_id}.{ext}'

			# samples are based on speakers.
			# there is always a speaker 0 by default.
			if 1 >= int (voice_details['num_speakers']):
				speaker_url = build_sample_url (voice_base_url, 'speaker', 0)
				download_info['samples'].append (speaker_url)
			else:
				for speaker_name in voice_details['speaker_id_map']:
					speaker_id = int(voice_details['speaker_id_map'][speaker_name])
					speaker_url = build_sample_url (voice_base_url, 'speaker', speaker_id)
					download_info['samples'].append (speaker_url)

			return download_info
		else:
			holz.error (f'Invalid voice index!')
	else:
		holz.error (f'Cannot recognize: "{code}"')

	return None


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
		holz.info (f'Best guess for "{target_lang}": {matching_code} ({lang["name_native"]} [{lang["name_english"]}])')
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

	with open (p.as_posix (), 'w') as f:
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
		for model in db.model_list_installed (context['paths']):
			sys.stdout.write (f"\t{model['code']}:{model['name']}@{model['quality']}")
			if args.verbose:
				sys.stdout.write (f"\t{model['path']}")
			sys.stdout.write ("\n")

		return 0
	
	if args.all:
		for code in langdb:
			lang = langdb[code]

			sys.stdout.write (f'Voices for "{code}":\n')
			voice_i = 0
			for voice_name in lang['voices']:
				sys.stdout.write (f"\t{voice_i}: {voice_name}\n")

				voice_i = voice_i + 1

		return 0

	code = args.language_code
	if not code in langdb:
		holz.error (f'Could not find language with code "{code}".')
		return 13

	lang = langdb[code]
	voice_i = args.voice_index
	index = context['db']['index']

	if -1 < voice_i:
		voice_name = lang['voices'][voice_i]

		sys.stdout.write (f'{voice_name}\t{voice_i}\n')
		speakers = index[voice_name]['speaker_id_map']
		sys.stdout.write (f'Speakers:\n')
		if 0 == len (speakers):
			sys.stdout.write (f'\t\t0 (no-name)\n')
		else:
			for speaker_id in speakers:
				sys.stdout.write (f'\t\t{speakers[speaker_id]:3} ({speaker_id})\n')
	else:
		sys.stdout.write (f'Available voices ({code}):\n')
		voice_i = 0
		for voice_name in lang['voices']:
			sys.stdout.write (f"\t{voice_i}: {voice_name}\n")

			voice_i = voice_i + 1

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
	index = context['db']['index']
	langdb = context['db']['languages']
	
	holz.info (f'Looking up preview info for {code}:{voice_i}:{speaker_i} ...')
	speaker_url = None
	download_info = _assemble_download_info (context, code, voice_i)
	if download_info:
		if -1 < speaker_i and speaker_i < len (download_info['samples']):
			speaker_url = download_info['samples'][speaker_i]

	holz.debug (download_info)

	if not speaker_url:
		holz.error ('Could not find sample for this voice.')
		return 13

	local_voice_path = f"{context['paths']['voices']}/{download_info['local_path_relative']}"
	samples_path_abs = os.path.realpath (f"{local_voice_path}/samples")
	with pathlib.Path (samples_path_abs) as p:
		p.mkdir (parents=True, exist_ok=True)
		
		filename = os.path.basename (speaker_url)
		file_path = p.joinpath (filename)
		if file_path.exists ():
			holz.info ('Cached file detected.')
		else:
			holz.info (f'Downloading ({speaker_url}) ...')
			if dry_run:
				sys.stdout.write (f'dl {speaker_url} > {file_path.as_posix ()}\n')
			else:
				r = requests.get (speaker_url)
				if 300 > r.status_code:
					with open (file_path.as_posix (), 'wb') as f:
						f.write (r.content)
					holz.info ('Stored.')
				else:
					holz.error (f'Download broke with: {r}')
					return 13
		
		play_cmd = ['mplayer', file_path.as_posix ()]
		if dry_run:
			sys.stdout.write (f'Would play file via: "{" ".join (play_cmd)}"')
		else:
			if not file_path.exists ():
				holz.error ('File not found.')
				return 13

			sys.stderr.write (f'Playing {file_path.as_posix ()} ...\n')
			r = _run_program (play_cmd)
			holz.info (f'Finished with: {r[0]}')

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
	index = context['db']['index']
	langdb = context['db']['languages']

	download_info = _assemble_download_info (context, code, voice_i)
	if not download_info:
		holz.error ('Could not find any downloads for this configuration.')
		return 13

	local_voice_path = os.path.realpath (f"{context['paths']['voices']}/{download_info['local_path_relative']}")
	holz.info (local_voice_path)
	with pathlib.Path (local_voice_path) as p:
		p.mkdir (parents=True, exist_ok=True)

		config_url = download_info['config']['url']
		config_file_path = p.joinpath (os.path.basename (config_url))
		if not config_file_path.exists ():
			size = util.float_round (float (download_info['config']['size']) / 1024)
			holz.info (f'Fetching config ({size}kb) ...')
			if not dry_run:
				"""
				r = requests.get (config_url)
				if 300 > r.status_code:
					with open (config_file_path, 'wb') as f:
						f.write (r.content)
				else:
					holz.error ('Error downloading config.')
					return 13
				"""
				r = util.download_as_stream_with_progress (config_url, config_file_path.as_posix ())
				if 0 > r:
					holz.error ('Error downloading config.')
					return 13

		else:
			holz.info ('Config already cached.')

		model_url = download_info['model']['url']
		model_file_name = os.path.basename (model_url)
		model_name = model_file_name.split ('.')[0]
		model_file_path = p.joinpath (model_file_name)
		if not model_file_path.exists ():
			size = util.float_round (float (download_info['model']['size']) / 1024 / 1024)
			holz.info (f'Fetching {model_name} ({size}mb) ...')
			if not dry_run:
				"""
				r = requests.get (model_url)
				if 300 > r.status_code:
					with open (model_file_path, 'wb') as f:
						f.write (r.content)
				else:
					holz.error ('Error downloading model.')
					return 13
				"""
				r = util.download_as_stream_with_progress (model_url, model_file_path.as_posix ())
				if 0 > r:
					holz.error ('Error downloading model.')
					return 13
		else:
			holz.info ('Model already cached.')

		selector = download_info["selection_name"]
		sys.stdout.write (f'{selector}\t{model_name}\t{model_file_path}')

	return 0
