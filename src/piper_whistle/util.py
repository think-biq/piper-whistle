"""Utility functions.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.


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
