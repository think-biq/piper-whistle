"""
CLI tool to manage piper voices.
"""
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
# First import sys and pathlib needed for sys.path manipulation.
import sys
import pathlib
# Append root package to path so it can be called with absolute path.
sys.path.append (str (pathlib.Path(__file__).resolve().parents[1]))
# Then import local modules via absolute path.
from piper_whistle import cli
from piper_whistle import cmds
from piper_whistle import db
from piper_whistle import holz
from piper_whistle import search
from piper_whistle import util


def version ():
	return "1.6.78"


__all__ = ['cli', 'cmds', 'db', 'search', 'version']


if '__main__' == __name__:
	print (version ())
