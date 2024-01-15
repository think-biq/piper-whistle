# -*- coding: utf8 -*-
# Copyright (c) blurryroots innovation qanat OÜ All Rights Reserved.

FILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_DIR := $(realpath -s $(shell dirname $(FILE_PATH)))
SHELL := /bin/bash

audit:
	pip-audit --desc
	pip-audit --fix --dry-run

lint:
	yamllint .gitlab-ci.yml
	flake8 \
		--ignore W191,E211,E128,E203,E124,F541,E402,E251,W504,W503 \
		"$(PROJECT_DIR)/src/piper_whistle"

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

pip-update-pip:
	python3 -m pip install -U pip

pip-install-dev:
	python3 -m pip install -r requirements.dev.txt

pip-install-runtime:
	python3 -m pip install -r requirements.txt

pip-update-all: pip-update-pip pip-install-dev pip-install-runtime

release:
	mkdir -p "$(PROJECT_DIR)/build/release"
	# https://github.com/pypa/setuptools/issues/3000
	# Add -n to allow build to use current package env
	PYTHONPATH=$(PWD) python3 -m build -s -n -w -o "$(PROJECT_DIR)/build/release"

pypi-test:
	$(PROJECT_DIR)/etc/./upload-pypi.sh \
		testpypi test.pypi.cfg "$(PROJECT_DIR)/build/release"/*

pypi:
	$(PROJECT_DIR)/etc/./upload-pypi.sh \
		pypi pypi.cfg "$(PROJECT_DIR)/build/release"/*

version:
	@python3 -m src.piper_whistle.version
