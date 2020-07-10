.PHONY: help setup generate test types format clean plugin full-test check-style

help:               ## - Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

# Dev workflow tasks

generate:           ## - Generate test cases (do this once before running test)
	poetry run python -m tests.generate

test:               ## - Run tests
	poetry run pytest --cov betterproto

types:              ## - Check types with mypy
	poetry run mypy src/betterproto --ignore-missing-imports

format:             ## - Apply black formatting to source code
	poetry run black . --exclude tests/output_

clean:              ## - Clean out generated files from the workspace
	rm -rf .coverage \
	       .mypy_cache \
	       .pytest_cache \
	       dist \
	       **/__pycache__ \
	       tests/output_*

# Manual testing

# By default write plugin output to a directory called output
o=output
plugin:             ## - Execute the protoc plugin, with output write to `output` or the value passed to `-o`
	mkdir -p $(o)
	poetry run python -m grpc.tools.protoc $(i) --python_betterproto_out=$(o)

# CI tasks

full-test: generate ## - Run full testing sequence with multiple pythons
	poetry run tox

check-style:        ## - Check if code style is correct
	poetry run black . --check --diff --exclude tests/output_
