# -*- coding: utf8 -*-
# Copyright (c) blurryroots innovation qanat OÜ All Rights Reserved.

FILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_DIR := $(realpath -s $(shell dirname $(FILE_PATH)))
SHELL := /bin/bash 


docs-build:
	make -C docs

run-tests:
	python3 -m unittest $(PROJECT_DIR)/src/testing/functional.py

venv-setup:
	python3 -m venv .

venv-clean:
	rm -rf bin build dist include lib lib64 piper_whistle.egg-info pyvenv.cfg share

venv-deactivate:
	$(shell declare -f deactivate && deactivate)

build-wheel:
	python3 "$(PROJECT_DIR)/setup.py" bdist_wheel
