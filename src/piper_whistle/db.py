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
import requests
import rich
import userpaths
import time
import urllib
import pathlib
from . import holz
from . import search


def data_paths ():
	"""! Query for data paths used by whistle.

	Provides a map of data paths used by whistle.
	
	* data: Root path of whistle data.
	* voices: Storage path for voice data.
	* index: Language details cached from huggingface repository (JSON).
	* languages: Language data lookup (JSON), built from index. Uses language code as keys.
	* last-updated: A flat file containig the timestamp when whistle data was refreshed last.
	

	@return Returns a map with respective paths.
	"""
	whistle_data_path = os.path.join (userpaths.get_appdata (), 'piper-whistle')
	whistle_voices_path = os.path.join (whistle_data_path, 'voices')
	whistle_voice_index = os.path.join (whistle_data_path, 'index.json')
	whistle_voice_lookup = os.path.join (whistle_data_path, 'languages.json')
	whistle_voice_timestamp = os.path.join (whistle_data_path, 'last-updated')
	return {
		'data': whistle_data_path,
		'voices': whistle_voices_path,
		'index': whistle_voice_index,
		'languages': whistle_voice_lookup,
		'last-updated': whistle_voice_timestamp
	}


def remote_repo_config ():
	"""! Returns information about the remote repository.

	The map return comes with the following fields.

	hf-root: Hugging Face root url.
	repo-id: Repository identifier (in format "username/reponame")
	branch: Branch name,
	voice-index: Path to voice index file (JSON). Relative to repository root.

	@return Returns a map with relevant repository information.
	"""
	return {
		'hf-root': 'https://huggingface.co',
		'repo-id': 'rhasspy/piper-voices',
		'branch': 'main',
		'voice-index': 'voices.json'
	}


def remote_repo_build_branch_root (repo_info):
	"""! Build repository root URL.
	
	The base URL will point to the root of the repository, including the branch.

	@param repo_info Remote repo information map. Can be obtained via @ref "remote_repo_config ()".
	@return Returns a list of file info maps with keys {path,size} or None on error.
	"""
	repo_root = f"{repo_info['hf-root']}/{repo_info['repo-id']}"
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
	r = requests.get (url)
	if 300 > r.status_code:
		return json.loads (r.content.decode ('utf8'))
	
	holz.error (f'Could not fetch "{url}"!')
	rich.inspect (r)
	return None


def index_download_and_rebuild (context):
	"""! Fetch latest voice index and build lookup database, then recreates context.

	It takes the current context map object, fetches the latest voice information,
	re-builds the cache / database, re-create the context and returns it.
	
	@param context Context map containig whistle index and language info. Can be created via @ref "context_create ()".
	
	@return Returns parse json object of voice index.
	"""
	paths = context['paths']
	repo_info = context['repo']

	with pathlib.Path (paths['data']) as p:
		p.mkdir (parents = True, exist_ok = True)

	with pathlib.Path (paths['voices']) as p:
		p.mkdir (parents = True, exist_ok = True)

	holz.info ('Fetching current index ...')
	index = index_fetch_raw (repo_info)
	if not index:
		holz.error ('Unable to build index.')
		return None

	with open (paths['index'], 'w') as f:
		json.dump (index, f, indent = 4)

	holz.info ('Rebuilding language database ...')
	langdb = {}
	for voice in index:
		l = index[voice]['languages']
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

	holz.info ('Regenerating context ...')
	return context_create (paths, repo_info)


def context_create (paths = data_paths (), repo_info = remote_repo_config ()):
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
	with open (paths['index'], 'r') as f:
		index = json.load (f)

	with open (paths['languages'], 'r') as f:
		langdb = json.load (f)

	return {
		'paths': paths,
		'db': {
			'index': index,
			'languages': langdb
		},
		'repo': repo_info
	}


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
			print (f'{needle} ~ {lang_code}')
			matching_code = lang_code
			break
		lang_name_native = langdb[lang_code]['name_native']
		matched, c = search.looks_like (needle, lang_name_native, 0.8)
		if matched:
			print (f'{needle} ~ {lang_name_native} (native)')
			matching_code = lang_code
			break
		lang_name_en = langdb[lang_code]['name_english']
		matched, c = search.looks_like (needle, lang_name_en, 0.8)
		if matched:
			print (f'{needle} ~ {lang_name_en} (english)')
			matching_code = lang_code
			break
		lang_country = langdb[lang_code]['country_english']
		matched, c = search.looks_like (needle, lang_country, 0.7)
		if matched:
			print (f'{needle} ~ {lang_country}')
			matching_code = lang_code
			break

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
	with pathlib.Path (paths['voices']) as p:
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
	with pathlib.Path (paths['voices']) as p:
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