"""Whistle database functionallity.

Defines functions to interact with the meta information / database of whistle.
All relevant files and paths can be accessed via "data_paths ()"

The index is refreshed by querying the hugging face repository "rhasspy/piper-voices"

Here's an example of how to identify different parts of a voice via URL

URL: https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_PT/tug%C3%A3o/medium/pt_PT-tug%C3%A3o-medium.onnx.json

	* root: https://huggingface.co/rhasspy/piper-voices
	* op: /resolve
	* branch: /main
	* code_short: /pt
	* code_long: /pt_PT
	* voice_name: /tug%C3%A3o
	* voice_quality: /medium
	* voice_config: /pt_PT-tug%C3%A3o-medium.onnx.json

"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import os
import sys
import json
import userpaths
import time
import urllib
import pathlib
import tempfile
# Append root package to path so it can be called with absolute path.
sys.path.append (str (pathlib.Path(__file__).resolve().parents[1]))
# ..
from piper_whistle import holz
from piper_whistle import util
from piper_whistle import search


def data_paths (appdata_root_path = userpaths.get_appdata ()):
	"""! Query for data paths used by whistle.

	Provides a map of data paths used by whistle.
	
	* data: Root path of whistle data.
	* voices: Storage path for voice data.
	* index: Language details cached from huggingface repository (JSON).
	* languages: Language data lookup (JSON), built from index. Uses language code as keys.
	* last-updated: A flat file containig the timestamp when whistle data was refreshed last.
	
	@param config_root_path Path to the directory, where applications can store configuration and data.
	@return Returns a map with respective paths.
	"""
	whistle_data_path = pathlib.Path (appdata_root_path).joinpath ('piper-whistle')
	return {
		'data': whistle_data_path.as_posix (),
		'repo': whistle_data_path.joinpath ('repo.json').as_posix (),
		'voices': whistle_data_path.joinpath ('voices').as_posix (),
		'index': whistle_data_path.joinpath ('index.json').as_posix (),
		'languages': whistle_data_path.joinpath ('languages.json').as_posix (),
		'last-updated': whistle_data_path.joinpath ('last-updated').as_posix ()
	}


def remote_repo_config (paths):
	"""! Returns information about the remote repository.

	The map return comes with the following fields.

	root: Repository root url (e.g. huggingface).
	repo-id: Repository identifier (in format "username/reponame")
	branch: Branch name,
	voice-index: Path to voice index file (JSON). Relative to repository root.

	@return Returns a map with relevant repository information.
	"""
	repo = None
	repo_config_file = pathlib.Path (paths['repo'])
	if not repo_config_file.exists ():
		repo = {
			'root': 'https://huggingface.co',
			'repo-id': 'rhasspy/piper-voices',
			'branch': 'main',
			'voice-index': 'voices.json'
		}
		holz.debug (f'Writing default repo config to "{repo_config_file}" ...')
		# Make sure data root path exists, in case repo config is the first to use it.
		repo_config_file.parent.mkdir (parents = True, exist_ok = True)
		with open (repo_config_file, 'w') as f:
			json.dump (repo, f, indent = 4)

	holz.debug (f'Loading repo config from "{repo_config_file}" ...')
	with open (repo_config_file, 'r') as f:
		repo = json.load (f)

	return repo


def remote_repo_build_branch_root (repo_info):
	"""! Build repository root URL.
	
	The base URL will point to the root of the repository, including the branch.

	@param repo_info Remote repo information map. Can be obtained via @ref "remote_repo_config ()".
	@return Returns a list of file info maps with keys {path,size} or None on error.
	"""
	repo_root = f"{repo_info['root']}/{repo_info['repo-id']}"
	branch_root = f"{repo_root}/resolve/{repo_info['branch']}"

	return branch_root


def remote_repo_build_index_url (repo_info):
	"""! Build URL pointing to repository voice index file.

	This will produce the link to the voices.json index file, which will be used
	to build whistle database and lookup.

	@param repo_info Remote repo information map. Can be obtained via @ref "remote_repo_config ()".
	@return Returns a list of file info maps with keys {path,size} or None on error.
	"""
	branch_root = remote_repo_build_branch_root (repo_info)
	index_url = f"{branch_root}/{repo_info['voice-index']}"

	return index_url


def assemble_download_info (context, code, voice_i):
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
	base_url = remote_repo_build_branch_root (context['repo'])

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
				'card': None,
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
				elif file.endswith ('MODEL_CARD'):
					download_info['card'] = {
						'url': f'{base_url}/{file}',
						'size': voice_details['files'][file]['size_bytes'],
						'md5': voice_details['files'][file]['md5_digest']
					}

			# Get voice URL where path is one layer up (omitting model name).
			voice_base_url = util.url_path_cut (download_info['model']['url'], 1)

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


def _fetch_url_raw (url):
	"""
	"""
	temp = tempfile.NamedTemporaryFile ()
	temp_path = temp.name
	temp.close ()

	r = util.download_as_stream_with_progress (url, temp_path)
	if 0 < r:
		holz.debug (f'Finished downloading. "{url}" => "{temp_path}"')
		with open (temp_path, 'r') as f:
			return f.read ()

	return None


def index_fetch_raw_filelist (repo_info):
	"""! Query the huggingface repository for a list of model files.
	@param repo_info Remote repo information map. Can be obtained via @ref "remote_repo_config ()".
	@return Returns a list of file info maps with keys {path,size} or None on error.
	"""
	import huggingface_hub as hf

	api = hf.HfApi ()

	repo_id = repo_info['repo-id']
	r = api.model_info (repo_id, files_metadata = True)
	if 300 > r.status_code:
		filelist = []
		for file in r.siblings:
			filelist.append ({ 'path': file.rfilename, 'size': file.size })

		return filelist
	
	holz.error (f'Could not fetch raw list from "{repo_id}".')
	return None


def index_fetch_raw (repo_info):
	"""! Query the huggingface repository for most recent voice index.
	@param repo_info Remote repo information map. Can be obtained via @ref "remote_repo_config ()".
	@return Returns parse json object of voice index.
	"""
	url = remote_repo_build_index_url (repo_info)

	raw_text = _fetch_url_raw (url)
	if raw_text:
		return json.loads (raw_text)

	holz.error (f'Could note fetch index.')
	return None


def _parse_model_card (card_text):
	lines = [line.strip () for line in card_text.split ('\n')]
	entry = {
		'dataset-url': None,
		'license': None,
		'training': None,
		'reference': None
	}

	read_training_status = False
	ln = 0
	for line in lines:
		if 0 == len (line):
			continue

		if read_training_status:
			l = line.lower ()
			if l.startswith ('finetuned'):
				entry['training'] = 'Tuned'
				entry['reference'] = line.replace ('Finetuned from', '').strip ()
			elif l.startswith ('fine-tuned'):
				entry['training'] = 'Tuned'
				entry['reference'] = line.replace ('Fine-tuned from', '').strip ()
			else:
				entry['training'] = 'Original'
				entry['reference'] = line.replace ('Trained from scratch', '')
				if entry['reference'].endswith ('.'):
					entry['reference'] = entry['reference'][:-1]
			read_training_status = False
		elif line.startswith ('* License:'):
			entry['license'] = line.replace ('* License:', '').strip ()
		elif line.startswith ('* URL:'):
			entry['dataset-url'] = line.replace ('* URL:', '').strip ()
		elif line.startswith ('## Training'):
			read_training_status = True
		ln += 1

	return entry


def index_download_and_rebuild (paths, repo_info):
	"""! Fetch latest voice index and build lookup database, then recreates context.

	Using the info on data paths and remote repository, it fetches the latest
	voice information, re-builds the cache / database, creates a context
	and returns it.
	
	@param context Context map containig whistle index and language info.
	               Can be created via @ref "context_create ()".
	
	@return Returns parse json object of voice index.
	"""
	holz.debug ('Ensuring data paths exists ...')

	# Make sure data path exists.
	pathlib.Path (paths['data']).mkdir (parents = True, exist_ok = True)

	# Make sure voice data storage path exists.
	pathlib.Path (paths['voices']).mkdir (parents = True, exist_ok = True)

	holz.info ('Fetching current index ...')
	index = index_fetch_raw (repo_info)
	if not index:
		holz.error ('Unable to build index.')
		return None

	holz.info (f"Storing index at '{paths['index']}' ...")
	with open (paths['index'], 'w') as f:
		json.dump (index, f, indent = 4)

	holz.info ('Rebuilding language database ...')
	langdb = {}
	for voice in index:
		l = index[voice]['language']
		if not (l['code'] in langdb):
			langdb[l['code']] = l
			langdb[l['code']]['voices'] = []
		langdb[l['code']]['voices'].append (index[voice]['key'])
	
	with open (paths['languages'], 'w') as f:
		json.dump (langdb, f, indent = 4)

	holz.info ('Updating timestamp ...')
	last_update = time.time ()
	with open (paths['last-updated'], 'w') as f:
		f.write (f'{last_update}')

	holz.info (f"Database files stored at '{paths['data']}'.")

	# build legal info based on model cards
	legal = {}
	if True:
		base_url = remote_repo_build_branch_root (repo_info)

		for code in langdb:
			holz.info (f'Processing "{code}":')				
			voice_i = 0
			for voice_name in langdb[code]['voices']:
				holz.info (f"\tFetching model card for {voice_i}: {voice_name}")
				dl_info = None
				voice_details = index[voice_name]
				# Identify onnx speech model files.
				for file in voice_details['files']:
					if file.endswith ('MODEL_CARD'):
						dl_info = {
							'url': f'{base_url}/{file}',
							'size': voice_details['files'][file]['size_bytes'],
							'md5': voice_details['files'][file]['md5_digest']
						}

				model_card_text = _fetch_url_raw (dl_info['url'])
				card = _parse_model_card (model_card_text)

				holz.info (f'\tStoring license ...')
				legal[voice_name] = card

				voice_i = voice_i + 1

		dp = pathlib.Path (paths['data'])
		dp = dp.joinpath ('legal.json')
		with open (dp, 'w') as f:
			json.dump (legal, f, indent = 4)

	holz.info ('Regenerating context ...')
	context = context_create (paths, repo_info)

	"""TODO: consider automatic lookup / best guess of corpus data
	# https://raw.githubusercontent.com/coqui-ai/open-speech-corpora/master/README.md
	"""
	return context


def _context_is_valid (context):
	paths_ok = ('paths' in context)
	if not paths_ok:
		holz.warn ('Data paths appear corrupt.')
	db_ok = ('db' in context \
		and ('index' in context['db'] and dict == type (context['db']['index'])) \
		and ('languages' in context['db'] and dict == type (context['db']['languages'])) \
	)
	if not db_ok:
		holz.warn ('It appears db is corrupt.')
	repo_ok = ('repo' in context)
	if not repo_ok:
		holz.warn ('Remote repository info appears corrupt.')

	return paths_ok \
		and  db_ok \
		and repo_ok


def context_create (paths, repo_info):
	"""! Creates context map object.

	Loads and parses whistle JSON databases (raw index and language lookup).

	Returs a map containing:
	
	* paths: Data paths. See @ref "data_paths ()".
	* db: Voice and languages information. Contains following keys:
		* index: Voice index fetched from huggingface repository.
		* language: Generated language lookup to select voices by language code.
	* repo: Repo config. See @ref "remote_repo_config ()".
	
	@param paths Paths map. Can be obtained via @ref "data_paths ()".
	@param repo_info Remote repo information map. Can be obtained via @ref "remote_repo_config ()".

	@return Returns voice and language lookups.
	"""
	db = {
		'index': None,
		'languages': None
	}

	p_index = pathlib.Path (paths['index'])
	if not p_index.exists ():
		holz.error ('No database index found!')
	else:
		with open (p_index, 'r') as f:
			db['index'] = json.load (f)

	p_languages = pathlib.Path (paths['languages'])
	if not p_languages.exists ():
		holz.error ('No language lookup found!')
	else:
		with open (p_languages, 'r') as f:
			db['languages'] = json.load (f)

	lgl_path = pathlib.Path (paths['data'])
	lgl_path = lgl_path.joinpath ('legal.json')
	if not lgl_path.exists ():
		holz.error ('No legal lookup found!')
	else:
		with open (lgl_path, 'r') as f:
			db['legal'] = json.load (f)

	context = {
		'paths': paths,
		'db': db,
		'repo': repo_info
	}

	if not _context_is_valid (context):
		return None
	
	return context


def context_guess_language_from_name (context, needle):
	"""! Searches the index and language lookup for a language which comes closest to your query.

	The search is done via fuzzy matching, trying to find the closest resemblance
	of the language or country name you provided.

	@param context Context map containig whistle index and language info. Can be created via @ref "context_create ()".
	@param needle Search term. This will be matched against countries, language names, codes.

	@return Returns the corresponding country code, or None if no match could be found.
	"""
	langdb = context['db']['languages']
	matching_code = None	

	for lang_code in langdb:
		matched, c = search.looks_like (needle, lang_code, 0.91, False)
		if matched:
			holz.info (f'{needle} ~ {lang_code}')
			matching_code = lang_code
			break
		lang_name_native = langdb[lang_code]['name_native']
		matched, c = search.looks_like (needle, lang_name_native, 0.8)
		if matched:
			holz.info (f'{needle} ~ {lang_name_native} (native)')
			matching_code = lang_code
			break
		lang_name_en = langdb[lang_code]['name_english']
		matched, c = search.looks_like (needle, lang_name_en, 0.8)
		if matched:
			holz.info (f'{needle} ~ {lang_name_en} (english)')
			matching_code = lang_code
			break
		lang_country = langdb[lang_code]['country_english']
		matched, c = search.looks_like (needle, lang_country, 0.7)
		if matched:
			matching_code = lang_code
			holz.info (f'{needle} ~ {lang_country}')
			break

	holz.info (matching_code)

	return matching_code


def model_list_installed (paths):
	"""! Searches piper-whistle cache for all models installed.

	Checks the user cache path (i.e. ~/.config/piper-whistle on *nix)

	The returned list contains map object with the following keys:
	
	' name: Clean voice name.
	' quality: Voice quality.
	' code: Language / Country code. (e.g. en_GB)
	' path: The absolute path to the onnx model.

	@param context Context map containig whistle index and language info. Can be created via @ref "context_create ()".

	@return Returns a list containing all installed models.
	"""
	models = []
	p = pathlib.Path (paths['voices'])
	for lang_dir in p.iterdir ():
		code = lang_dir.name
		for voice_dir in lang_dir.iterdir ():
			onnx_file_path = voice_dir.joinpath (f'{voice_dir.name}.onnx')
			if not onnx_file_path.exists ():
				continue

			# name has language code prepended. remove.
			rest = voice_dir.name.replace (f'{code}-', '')
			# now split off quality
			voice_name, voice_quality = rest.split ('-')
			models.append ({
				'name': voice_name,
				'quality': voice_quality,
				'code': code,
				'path': onnx_file_path.as_posix ()
			})

	return models


def model_resolve_path (paths, model_info):
	"""! Searches piper-whistle cache for a model corresponding to given specs.

	Checks the user cache path (i.e. ~/.config/piper-whistle on *nix) for a model
	constraied by given name, quality and speaker.

	The returned list contains map object with the following keys:
	
	* name: Clean voice name.
	* quality: Voice quality.
	* code: Language / Country code. (e.g. en_GB)
	* path: The absolute path to the onnx model.

	@param paths Paths map. Can be obtained via @ref "data_paths ()".
	@param model_info Map containing name, quality and speaker.

	@return Returns the path to the model, or None if nothing is found.
	"""
	name = model_info['name']
	quality = model_info['quality']
	speaker = model_info['speaker']

	voice_file_path = None
	p = pathlib.Path (paths['voices'])
	for lang_dir in p.iterdir ():
		code = lang_dir.name
		for voice_dir in lang_dir.iterdir ():
			# name has language code prepended. remove.
			rest = voice_dir.name.replace (f'{code}-', '')
			# now split off quality
			voice_name, voice_quality = rest.split ('-')
			if voice_name == name and voice_quality == quality:
				filename = f'{voice_dir.name}.onnx'
				voice_file_path = voice_dir.joinpath (filename).as_posix ()
				break

	return voice_file_path


def model_remove (paths, model_info):
	"""! Removes given model from piper-whistle cache.

	@return Returns the true if remove, false otherwise.
	"""
	model_path = model_resolve_path (paths, model_info)
	if not model_path:
		holz.warn (f'Could not find model with name "{model_info["name"]}@{model_info["quality"]}".')
		return False

	p = pathlib.Path (model_path)
	pr = p.resolve ().parent
	
	for model_part in pr.iterdir ():
		holz.debug (f'Removing "{model_part}" ...')
		model_part.unlink ()

	holz.debug (f'Removing "{pr}" ...')
	pr.rmdir ()

	sys.stdout.write (f'Removed "{model_info["name"]}@{model_info["quality"]}".\n')

	return True
