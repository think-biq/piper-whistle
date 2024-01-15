"""Utility functions.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import sys
import pathlib
import requests
import urllib.parse
from tqdm import tqdm
# Append root package to path so it can be called with absolute path.
sys.path.append (str (pathlib.Path(__file__).resolve().parents[1]))
# Then import whistle module with absolute path.
from piper_whistle import holz


def url_path_cut (url: str, count: int
	, retain_query : bool = False
	, retain_fragment : bool = False
	, retain_params : bool = False
):
	"""! Takes a URL and cuts of a certain number of path elements.

	If no path elements left, will return base url, regardless of how many
	more cuts are requested. You may retain URL elements by setting the
	retain flags. Otherwise the URL will be simplified to only scheme,
	host and path.

	@param url String of url to parse.
	@param retain_query Keeps query part of URL. (default False)
	@param retain_fragment Keeps fragment part of URL. (default False)
	@param retain_params Keeps params part of URL. (default False)
	@return A string of the cut URL.
	"""
	purl = urllib.parse.urlparse (url)

	splitpath = purl.path.split ('/')
	cutpath = '/'.join (splitpath[:-count]) if 1 < len (splitpath) else ''
	purlmod = urllib.parse.ParseResult (
		scheme = purl.scheme,
		netloc = purl.netloc,
		path = cutpath,
		query = purl.query if retain_query else '',
		fragment = purl.fragment if retain_fragment else '',
		params = purl.params if retain_params else ''
	)

	return urllib.parse.urlunparse (purlmod)


def url_path_split (url : str):
	"""! Takes a URL and splits the path elements into list elements.
	@param url String of url to parse.
	@return A list of parts comprising the path element of the URL.
	"""
	purl = urllib.parse.urlparse (url)
	return purl.path.split ('/')[1:]


def float_round (x : float, digits : int = 2):
	"""! Rounds given number to a specific precision
	@param x Number to round.
	@param digits The number of significant digitis to retain. Default is 2.
	@return Returns x rounded to significant digits.
	"""
	k = 10**digits
	xx = int (x * k)
	x = float (xx) / k
	return x


def download_as_stream_with_progress (
	url: str, file_path: str, label: str = 'dl'
):
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
			rich.inspect (resp)
		except Exception as e:
			holz.debug (str (e))
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
