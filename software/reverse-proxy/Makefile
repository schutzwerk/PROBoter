SHELL := /bin/bash
VERSION ?= latest

# The directory of this file
DIR := $(shell echo $(shell cd "$(shell  dirname "${BASH_SOURCE[0]}" )" && pwd ))

CONTAINER_NAME ?= proboter-reverse-proxy

start: ## Start with development config
	sudo docker run \
		-it \
		--rm \
		--name proboter-reverse_proxy_dev \
		--net=host \
		-e WEB_UI_ROOT=localhost:3000 \
		-e PROJECT_STORAGE_ROOT=localhost:5000 \
		-e PCB_ANALYSIS_ROOT=localhost:5001 \
		-e SIGNAL_ANALYSIS_ROOT=localhost:5002 \
		-e HARDWARE_CONTROL_ROOT=localhost:5003 \
		-v $(DIR)/nginx.conf:/etc/nginx/templates/default.conf.template:ro \
		-v $(DIR)/certs/fullchain.pem:/etc/nginx/ssl/live/proboter/fullchain.pem:ro \
		-v $(DIR)/certs/privkey.pem:/etc/nginx/ssl/live/proboter/privkey.pem:ro \
		nginx:latest

# This will output the help for each task
.PHONY: help

help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
.DEFAULT_GOAL := help
