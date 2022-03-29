SHELL := /bin/bash
VERSION ?= latest

# The directory of this file
DIR := $(shell echo $(shell cd "$(shell  dirname "${BASH_SOURCE[0]}" )" && pwd ))

IMAGE_NAME ?= schutzwerk/proboter-pcb_analysis
CONTAINER_NAME ?= proboter-pcb_analysis


init: ## Local dev. setup initialization
	pipenv --three && \
	pipenv install --dev pylint pytest coverage autopep8 schema rope matplotlib && \
	pipenv install -e .

lint: ## Source code linting
	pipenv run python -m pylint pcb_analysis

format: ## Source code formatting according to PEP8
	pipenv run autopep8 -r -i pcb_analysis

unit-test: ## Run unit tests
	pipenv run python -m pytest -v

coverage: ## Run unit tests with code coverage
	pipenv run coverage run --omit "config*.py" -m pytest -v && \
	pipenv run coverage report

start: ## Start the PCB analysis server
	export FLASK_APP=pcb_analysis && \
	export FLASK_ENV=development && \
	pipenv run flask run -h 127.0.0.1 -p 5001

# Build the container
image-build: ## Build the image
	sudo docker build --rm -t $(IMAGE_NAME):$(VERSION) .

image-build-nc: ## Build the image without caching
	sudo docker build --rm --no-cache -t $(IMAGE_NAME) .

image-remove-force: ## Remove the latest image (forced)
	sudo docker rmi -f $(IMAGE_NAME):$(VERSION)

container-run: ## Run container
	sudo docker run \
    -it \
		--name $(CONTAINER_NAME) \
		--net=host \
		$(IMAGE_NAME):$(VERSION)

container-stop: ## Stop a running container
	sudo docker stop $(CONTAINER_NAME)

container-remove: ## Remove a (running) container
	sudo docker rm -f $(CONTAINER_NAME)

container-restart: ## Restart the container
	make container-remove; \
	make container-run


# This will output the help for each task
.PHONY: help

help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
.DEFAULT_GOAL := help
