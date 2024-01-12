#!/bin/bash

build_debian_url () {
	# https://stackoverflow.com/a/53176862
	local tag=${1}
	local root="https://pypi.debian.net"
	local package_name="piper-whistle"
	local file_name="piper_whistle-${tag}-py3-none-any.whl"
	local url="${root}/${package_name}/${file_name}"

	echo ${url}
	return 0
}

main () {
	local tag=${1}
	local url=$(build_debian_url ${tag})

	local retries=33
	local cache=$(mktemp)
	
	# Try to resolve redirection via header lookup.
	if ! wget \
		--max-redirect=${retries} -nv --server-response \
		--spider --tries 1 ${url} 2> ${cache} 1> /dev/null
	then
		echo "Error fetching header info for ${url} ($?)!"
		return 13
	fi

	# Look at last line, fourth place space separate for resolved URL.
	tail -n 1 "${cache}" | awk '{ print $4 }'
	return 0
}

main $*
