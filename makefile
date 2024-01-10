# -*- coding: utf8 -*-
# Copyright (c) blurryroots innovation qanat OÜ All Rights Reserved.

FILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_DIR := $(realpath -s $(shell dirname $(FILE_PATH)))
SHELL := /bin/bash 


#	$(shell python3 "$(PROJECT_DIR)/build-config.py" \
#		$(shell python3 "$(PROJECT_DIR)/../src/piper_whistle/__init__.py") \
#		"$(PROJECT_DIR)/docs.cfg"\
#		"$(PROJECT_DIR)/docs.cfg.live")

readme-build:
	python3 tmplr build-readme \
		"$(PROJECT_DIR)/etc/readme.md.tmpl" \
		"$(PROJECT_DIR)/readme.md"

docs-build: readme-build
	python3 tmplr build-docs-cfg \
		"$(PROJECT_DIR)/etc/docs.cfg.tmpl" \
		"$(PROJECT_DIR)/docs/docs.cfg"
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

release:
	mkdir -p "$(PROJECT_DIR)/build/release"
	python3 -m build -s -w -o "$(PROJECT_DIR)/build/release"

pypi-test:
	twine upload -r testpypi "$(PROJECT_DIR)/build/release"/*

pypi:
	twine upload "$(PROJECT_DIR)/build/release"/*
