#!/bin/bash
# Copyright (c) 2023-∞ blurryroots innovation qanat OÜ
# Looks for version based on tag attached to current commit. Otherwise uses
# version lookup provided by makefile.

_script_dir=$(dirname $(realpath $0))

query-version () {
	local r=0

	pushd "${_script_dir}/.." > /dev/null
		if ! make version; then
			echo "Could not run version target in makefile." > /dev/stderr
			r=13
		fi
	popd > /dev/null

	return ${r}
}

main () {
	local r=0
	local tagname=$(mktemp)

	if ! git tag --points-at HEAD > ${tagname}; then
		echo "Git should not fail :/" > /dev/stderr
		return 13
	fi

	local tag=$(cat ${tagname})
	if (( 0 < ${#tag} )); then
		echo $(cat ${tagname})
	else
		if ! query-version > ${tagname}; then
			return $?
		fi

		r=$?
		echo $(cat ${tagname})
	fi

	return ${r}
}

main $*
