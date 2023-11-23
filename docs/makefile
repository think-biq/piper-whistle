# -*- coding: utf8 -*-
# Copyright (c) blurryroots innovation qanat OÜ All Rights Reserved.

FILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_DIR := $(realpath -s $(shell dirname $(FILE_PATH)))

release: build
	rm -rf "$(PROJECT_DIR)/published"/*
	cp -Rav "$(PROJECT_DIR)/html"/* "$(PROJECT_DIR)/published"

build: clean
	mkdir -p "$(PROJECT_DIR)/published"
	doxygen "$(PROJECT_DIR)/docs.cfg" \
		> "$(PROJECT_DIR)/docs.log" \
		2> "$(PROJECT_DIR)/docs.err.log"

clean:
	rm -rf "$(PROJECT_DIR)/html"
	rm -f "$(PROJECT_DIR)"/docs*.log
