# Every check runs through the GitHub workflow with act, so CI and local runs are the same thing.
ACT ?= act
PYTHON_VERSION ?= 3.13
BUILD := $(ACT) workflow_dispatch -W .github/workflows/build.yml --env NODE_OPTIONS=--no-network-family-autoselection

.PHONY: test test-all lint package check clean

test:
	$(BUILD) -j test --matrix python:$(PYTHON_VERSION)

test-all:
	$(BUILD) -j test

lint:
	$(BUILD) -j lint

package:
	$(BUILD) -j package

check:
	$(BUILD)

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .coverage
