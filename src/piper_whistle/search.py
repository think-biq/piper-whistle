"""Search tools

Utilities for fuzzy searching / comparison.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
from thefuzz import fuzz as fuzz_core


def looks_like (needle, haystack, threshold = 0.66, case_sensitive = True):
	"""! Fuzzy comparison / containment check.

	Takes a needle and searches haystack for the closest partial match given
	a specific threshold and case-mode.

	@param needle Search phrase.
	@param haystack	Corpuse to search in.
	@param threshold Match coefficient [0,1] Higher values force stricter closeness.
	@param case_sensitive Wheter to care for case differences.

	@return Returns a touple of whether match occurs, and the confidence coefficient.
	"""
	if not case_sensitive:
		needle = needle.lower ()
		haystack = haystack.lower ()

	confidence = fuzz_core.partial_ratio (needle, haystack)
	confidence /= 100.0

	return threshold < confidence, confidence
