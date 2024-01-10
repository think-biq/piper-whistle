"""CLI tool to manage piper voices.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
from . import cli
from . import cmds
from . import db
from . import holz
from . import search
from . import util


def version ():
	return "1.6.78"


if '__main__' == __name__:
	print (version ())
