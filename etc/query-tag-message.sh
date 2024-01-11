#!/bin/bash
# Copyright (c) 2023-∞ blurryroots innovation qanat OÜ
# Takes an existing git tag and prints the message to stdout.

main () {
	local tagname="$1"
	if ! git rev-list "${tagname}" 2> /dev/null > /dev/null; then
		echo Tag "${tagname}" not found.
		return 13
	fi

	local tagmsg=$(git tag -n33 -l ${tagname} \
		| awk {'first = $1; $1=""; print $0'} \
		| sed 's/^ //g')

	echo "${tagmsg}"
	return 0
}

main $*
