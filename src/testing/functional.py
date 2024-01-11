"""Functional testing of some core features.

Simulates calling whistle as CLI.
Test cases are called in order. It first builds the local database, then
downloads a voice file and queries some data related to the voice.

Initial setup is done in the setUpClass static (class-wide) function. It sets
up a temporary directory, which is used as app data root for whistle. All

"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
from ..piper_whistle import cli as whistle_cli
from ..piper_whistle import db as whistle_db
import unittest
from unittest.mock import patch
import sys
import tempfile
import os
import pathlib
import io
import re
from contextlib import redirect_stdout
from unittest import TestCase
from directory_tree import display_tree


expected_list_languages = """
ar_JO
ca_ES
cs_CZ
da_DK
de_DE
el_GR
en_GB
en_US
es_ES
es_MX
fi_FI
fr_FR
hu_HU
is_IS
it_IT
ka_GE
kk_KZ
lb_LU
ne_NP
nl_BE
nl_NL
no_NO
pl_PL
pt_BR
pt_PT
ro_RO
ru_RU
sk_SK
sr_RS
sv_SE
sw_CD
tr_TR
uk_UA
vi_VN
zh_CN
"""

expected_list_voice = """
de_DE-eva_k-x_low	0
Speakers:
		0 (no-name)
"""
expected_list_voice_plus_legal = """
de_DE-eva_k-x_low	0	Voice[Original]: See URL, Reference: , Dataset: https://www.caito.de/2019/01/03/the-m-ailabs-speech-dataset/
Speakers:
		0 (no-name)
"""


expected_install_voice = [
	'de_DE:eva_k@x_low',
	'de_DE-eva_k-x_low',
	'piper-whistle/voices/de_DE/de_DE-eva_k-x_low/de_DE-eva_k-x_low.onnx'
]


expected_list_installed_voices = """
	de_DE:eva_k@x_low
"""


expected_show_path = """
	piper-whistle/voices/de_DE/de_DE-eva_k-x_low/de_DE-eva_k-x_low.onnx
"""

expected_remove_voice = """
Removed "eva_k@x_low".
"""


def check_if_timestamp (result):
	m = re.match(r'^\d+\.\d+$', result)
	return not (m is None)


class CliCommandTests (unittest.TestCase):
	""" Using goofy naming scheme for test case ordering.
	Suggested here https://stackoverflow.com/a/7085051
	"""

	@classmethod
	def setUpClass (cls):
		# TestCase wide setup (as opposed to individual test based setUp ())
		sys.stdout.write (f'[Setup] Creating environemnt for "{cls}" ...\n')

		# Create a temporary app data root directory
		cls.tmp_dir = tempfile.TemporaryDirectory ()
		cls.data_root_path = pathlib.Path (cls.tmp_dir.name)
		cls.data_root_path.mkdir (parents = False, exist_ok = True)

		# Setup CLI argument list for every test procedure.
		data_root = cls.data_root_path.as_posix ()
		app_name = 'whistle'
		def make_cli_arg_list (*params):
			return [app_name, '-P', data_root, *list (params)]
		cls.test_arguments = {
			'create-index': make_cli_arg_list ('refresh', '-v'),
			'list-languages': make_cli_arg_list ('list', '-L'),
			'list-voice': make_cli_arg_list ('list', '-l', 'de_DE', '-i', '0'),
			'list-voice-legal': make_cli_arg_list ('list', '-l', 'de_DE', '-i', '0', '-g'),
			'install-voice': make_cli_arg_list ('install', 'de_DE', '0'),
			'list-installed-voices': make_cli_arg_list ('list', '-I'),
			'show-path': make_cli_arg_list ('path', 'de_DE-eva_k-x_low'),
			'remove-voice': make_cli_arg_list ('remove', 'de_DE-eva_k-x_low')
		}

		sys.stdout.write (f'[Setup] Temporary data root: "{data_root}"\n')

	@classmethod
	def tearDownClass (cls):
		sys.stdout.write (f'\n[Teardown] Data directory after running tests:\n')
		display_tree (cls.data_root_path.as_posix ())

	def _run_whistle_main (self, args):
		cli_output = io.StringIO ()
		with redirect_stdout (cli_output):
			with patch.object (sys, 'argv', args):
				whistle_cli.main (args)

		out_str = cli_output.getvalue ().strip ()
		return out_str

	def _run_whistle_main_with (self, arg_list_name):
		out_str = self._run_whistle_main (self.test_arguments[arg_list_name])
		return out_str

	def test_a0_create_index (self):
		# Ask whistle to downlnoad and rebuild voice database.
		out_str = self._run_whistle_main_with ('create-index')
		self.assertTrue (check_if_timestamp (out_str))

		whistle_paths = whistle_db.data_paths (self.data_root_path.as_posix ())
		self.assertTrue (os.path.exists (whistle_paths['data']))

	def test_b0_list_languages (self):
		# Ask whistle to list all available languages.
		out_str = self._run_whistle_main_with ('list-languages')

		self.assertEqual (out_str, expected_list_languages.strip ())

	def test_c0_list_voice (self):
		# Ask whistle to list the first voice for the german language.
		out_str = self._run_whistle_main_with ('list-voice')

		self.assertEqual (out_str, expected_list_voice.strip ())

	def test_d0_list_voice_legal (self):
		# Ask whistle to list the first voice for the german language and the
		# available legal information.
		out_str = self._run_whistle_main_with ('list-voice-legal')
		self.assertEqual (out_str, expected_list_voice_plus_legal.strip ())

	def test_e0_install_voice (self):
		# Ask whistle to install the first german voice at index 0.
		out_str = self._run_whistle_main_with ('install-voice')
		out_parts = out_str.split ('\t')

		self.assertEqual (out_parts[0], expected_install_voice[0])
		self.assertEqual (out_parts[1], expected_install_voice[1])
		self.assertTrue (out_parts[2].endswith (expected_install_voice[2]))

		whistle_paths = whistle_db.data_paths (self.data_root_path.as_posix ())
		onnx_path = os.path.join (whistle_paths['data']
			, expected_install_voice[2].replace ('piper-whistle/', '')
		)
		self.assertTrue (os.path.exists (onnx_path))

	def test_f0_list_installed_voices (self):
		# Ask whistle to list all installed voices.
		out_str = self._run_whistle_main_with ('list-installed-voices')
		self.assertEqual (out_str, expected_list_installed_voices.strip ())

	def test_g0_show_voice_path (self):
		# Ask whistle to show the path to the voice with name 'de_DE-eva_k-x_low'.
		out_str = self._run_whistle_main_with ('show-path')
		self.assertTrue (out_str.endswith (expected_show_path.strip ()))

	def test_h0_remove_voice (self):
		# Ask whistle to remove voice named 'de_DE-eva_k-x_low'.
		out_str = self._run_whistle_main_with ('remove-voice')
		self.assertEqual (out_str, expected_remove_voice.strip ())


if __name__ == '__main__':
    unittest.main ()
