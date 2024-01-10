#!env python3
"""    
	setuptools script to install / build piper-whistle.

	2021-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
	See license.md for details.

	https://think-biq.com
"""

import setuptools
from src.piper_whistle import version

with open("readme.md", "r") as fh:
	long_description = fh.read()

setuptools.setup (
	name = "piper_whistle",
	version = version.as_string (),
	author = "biq",
	author_email = "sven.freiberg@biq.solutions",
	description = "CLI tool to manage piper voices.",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	keywords="text-to-speech piper voice model tool",
	url = "https://gitlab.com/think-biq/piper-whistle",
	package_dir = { 'piper_whistle': 'src/piper_whistle' },
	packages = ['piper_whistle'],
	classifiers = [
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires = '>=3.8',
	entry_points = {
		'console_scripts': [
			'piper_whistle = piper_whistle.cli:main_sys'
		],
	},
	install_requires = [
		'attrs==23.1.0',
		'certifi==2023.7.22',
		'charset-normalizer==3.3.2',
		'filelock==3.13.1',
		'fsspec==2023.10.0',
		'huggingface-hub==0.18.0',
		'idna==3.4',
		'mdurl==0.1.2',
		'playsound==1.3.0',
		'PyYAML==6.0.1',
		'rapidfuzz==3.5.1',
		'requests==2.31.0',
		'thefuzz==0.20.0',
		'tqdm==4.66.1',
		'typing_extensions==4.8.0',
		'urllib3==2.0.7',
		'userpaths==0.1.3',
	]
)