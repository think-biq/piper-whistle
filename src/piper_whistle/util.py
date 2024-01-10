"""Utility functions.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import sys
import pathlib
import requests
from tqdm import tqdm
# Append root package to path so it can be called with absolute path.
sys.path.append (str (pathlib.Path(__file__).resolve().parents[1]))
# ..
from piper_whistle import holz


def float_round (x, digits = 2):
	"""! Rounds given number to a specific precision
	@param x Number to round.
	@param digits The number of significant digitis to retain. Default is 2.
	@return Returns x rounded to significant digits.
	"""
	k = 10**digits
	xx = int (x * k)
	x = float (xx) / k
	return x


def download_as_stream_with_progress (url: str, file_path: str, label: str = 'dl'):
	"""! Downloads a resource via streaming get request and shows progress.
	@param url Target URL to download.
	@param file_path Path to store downloaded file to.
	@param label Annotation used when printing progress. 'dl' by default.
	@return Returns number of bytes downloaded, or -1 on error.
	"""
	resp = requests.get (url, stream = True)
	if not (300 > resp.status_code):
		holz.error (f'Could not fetch "{url}"! (c: {resp.status_code})')
		try:
			import rich
			rich.inspect (r)
		except:
			holz.error (
				f'Skipping verbose response logging. '
				f'Module "rich" not installed.'
			)

		return -1

	total = int (resp.headers.get ('content-length', 0))
	# Can also replace 'file' with a io.BytesIO object
	with open (file_path, 'wb') as file, tqdm (
		desc = label,
		total = total,
		unit = 'iB',
		unit_scale = True,
		unit_divisor = 1024,
	) as bar:
		for data in resp.iter_content (chunk_size = 1024):
			size = file.write (data)
			bar.update (size)

	return total
