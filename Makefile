help:               ##	- Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

# Dev workflow tasks

setup:              ##	- Setup the virtualenv with poetry
	poetry install -E compiler

generate:           ##	- Generate test cases (do this once before running test)
	poetry run ./betterproto/tests/generate.py

test:               ##	- Run tests
	poetry run pytest --cov betterproto

types:              ##	- Check types with mypy
	poetry run mypy betterproto --ignore-missing-imports

format:             ##	- Apply black formatting to source code
	poetry run black . --exclude tests/output_

clean:						  ## - Clean out generated files from the workspace
	rm -rf .coverage \
	       .mypy_cache \
	       .pytest_cache \
	       dist \
	       **/__pycache__ \
	       betterproto/tests/output_*

# Manual testing

# By default write plugin output to a directory called output
o=output
plugin:             ##	- Execute the protoc plugin, with output writte to `output` or the value passed to `-o`
	mkdir -p $(o)
	protoc --plugin=protoc-gen-custom=betterproto/plugin.py $(i) --custom_out=$(o)

# CI tasks

full-test: generate ##	- Run full testing sequence
	poetry run tox

check-style:        ##	- Check if code style is correct
	poetry run black . --check --diff --exclude tests/output_
