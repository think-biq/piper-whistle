"""
Handle version related information.
"""

# Define in common three component form.
MAJOR = 1
MINOR = 6
PATCH = 193


def as_list ():
	'''Returns the three components as list'''
	return [MAJOR, MINOR, PATCH]


def as_string ():
	'''Joins the version components separated by a . (dot)'''
	return ".".join ([str (comp) for comp in as_list ()])


if '__main__' == __name__:
	print (as_string ())
