SHELL := /bin/bash
VERSION ?= latest

# The directory of this file
DIR := $(shell echo $(shell cd "$(shell  dirname "${BASH_SOURCE[0]}" )" && pwd ))

IMAGE_NAME ?= schutzwerk/proboter-web-ui
CONTAINER_NAME ?= proboter-web-ui

start: ## Start the development server
	npm run dev

lint: ## Linting and type checking
	npm run lint
	npm run typecheck

format: ## Code formatting
	npm run format

# Build the container
image-build: ## Build the image
	sudo docker build --rm -t $(IMAGE_NAME):$(VERSION) .

image-build-nc: ## Build the image without caching
	sudo docker build --rm --no-cache -t $(IMAGE_NAME) .

image-remove-force: ## Remove the latest image (forced)
	sudo docker rmi -f $(IMAGE_NAME):$(VERSION)

container-run: ## Run container (with X-forwarding)
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

