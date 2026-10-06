# ==============================================================================
# Brandon Foster Portfolio Platform - Makefile
# Convenience alias wrapper delegating to Taskfile.yml
# ==============================================================================

.PHONY: help dev backend frontend docker test test-frontend test-all eval pipeline build clean

help:
	@task --list

dev:
	task dev

backend:
	task dev:backend

frontend:
	task dev:frontend

docker:
	task dev:docker

test:
	task test

test-frontend:
	task test:frontend

test-all:
	task test:all

eval:
	task mlops:eval

pipeline:
	task mlops:pipeline

build:
	task build

clean:
	task clean
