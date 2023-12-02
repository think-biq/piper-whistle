#!env python3
# 2023-∞ (c) blurryroots innovation qanat OÜ. All rights reserved.
import sys
import string


class CfgTmpl (string.Template):
	delimiter = ':?'


def main ():
	version_string = sys.argv[1]
	config_tmpl_path = sys.argv[2]
	config_live_path = sys.argv[3]

	tmpl = None
	with open (config_tmpl_path, 'r') as f:
		raw_str = f.read ()
		tmpl = CfgTmpl (raw_str)

	values = {
		'whistle_version': version_string
	}
	tmpl_str = tmpl.substitute (values)
	with open (config_live_path, 'w') as f:
		f.write (tmpl_str)

	return 0


if '__main__' == __name__:
	main ()
