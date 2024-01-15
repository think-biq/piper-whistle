#!/bin/bash

main () {
	if ! which twine > /dev/null; then
		echo "Could not find twine!" > /dev/stderr
	fi

	local repo="${1}"
	shift
	local configpath="${1}"
	shift

	twine upload --non-interactive --verbose \
		--config-file "${configpath}" -r ${repo} \
		--skip-existing \
		$*
}

main $*
