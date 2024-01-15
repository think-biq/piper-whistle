#!/bin/bash

main () {
	python3 -m pip install \
		--trusted-host test.pypi.org \
		--trusted-host test-files.pythonhosted.org \
		--index-url https://test.pypi.org/simple/ \
		--extra-index-url https://pypi.org/simple/ \
		$*
}

main $*
