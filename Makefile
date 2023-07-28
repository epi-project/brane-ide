# MAKEFILE
#   by Lut99
#
# Created:
#   28 Jul 2023, 13:39:51
# Last edited:
#   28 Jul 2023, 14:10:41
# Auto updated?
#   Yes
#
# Description:
#   Makefile for the Brane Jupyter Notebook kernel.
#   
#   This can be used to either generate the development kernel, with all the
#   required [Xues](https://github.com/jupyter-xeus/xeus) dependencies, or a
#   containerized Jupyter Server with everything installed.


##### ARGUMENTS #####
ifdef DEBUG
DEBUG := 1
else
DEBUG := 0
endif

ifndef LIBBRANE_CLI
# Define the arguments for its version & architecture
ifndef VERSION
VERSION := 1.0.0
endif

ifndef ARCH
ARCH := x86_64
endif
endif

ifndef BRANE_API
# The address of the remote brane-api service.
# Remember, the kernel lives in a container so using localhost has no effect
BRANE_API := http://localhost:50051
endif

ifndef BRANE_DRV
# The address of the remote brane-drv service.
# Remember, the kernel lives in a container so using localhost has no effect
BRANE_DRV := grpc://localhost:50053
endif

ifndef BRANE_NOTEBOOK_DIR
# The path to which the home folder in the runtime container is mapped.
BRANE_NOTEBOOK_DIR := ./notebooks
endif





##### DEVELOPMENT IMAGE #####
# Builds the development environmen image
dev-image:
	docker build --load --tag brane-ide-dev --target dev -f Dockerfile .

# Starts the development environment with all the C++ deps installed
start-dev: dev-image
	docker run -d --name brane-ide-dev -v ".":"/source" --entrypoint sleep brane-ide-dev infinity
	@echo "You can now open Code and connect to the 'brane-ide-dev' container"

# Stop the development environment
stop-dev:
	docker rm --force brane-ide-dev
	@echo "The 'brane-ide-dev' container has been destroyed. Run 'make start-dev' to start again."





##### RUNTIME IMAGE #####
/tmp/libbrane_cli.so:
	$if [[ -z "$(LIBBRANE_CLI)" ]]; then \
		address="https://github.com/epi-project/brane/releases/download/v$(VERSION)/libbrane_cli-$(ARCH).so"; \
		if [[ ! -z $(curl --version) ]]; then \
			downloader=curl; \
			download_cmd="$$downloader --output /tmp/libbrane_cli.so $$address";\
		elif [[ ! -z $(wget --version) ]]; then \
			downloader=wget; \
			download_cmd="$$downloader -O /tmp/libbrane_cli.so $$address";\
		else \
			>&2 echo "No `curl` or `wget` found; install either, or manually specify a compatible `libbrane_cli.so` executable using the `LIBRRANE_CLI=...` option"; \
			exit 1; \
		fi \
		echo "Downloading BraneScript compiler library from '$$address' with $$downloader..."; \
		bash -c "$$download_cmd" || exit $?; \
	else \
		ln -s "$(LIBBRANE_CLI)" /tmp/libbrane_cli.so; \
	fi

runtime-image: /tmp/libbrane_cli.so
	@if [[ -z "$(LIBBRANE_CLI)" ]]; then \
		echo "Building 'brane-ide' image with downloaded BraneScript library..."; \
		# docker build --load -t "brane-ide" --target brane-ide-download --build-arg "VERSION=$(VERSION)" --build-arg "ARCH=$(ARCH)" -f Dockerfile . ; \
		echo "TODO"; \
	else \
		echo "Building 'brane-ide' image with local BraneScript library '$(LIBRRANE_CLI)'..."; \
		mkdir -p ".tmp"; \
		cp "$(BRANEC)" ".tmp/branec"; \
		docker build --load -t "brane-ide" --target brane-ide-local --build-arg "SOURCE=.tmp/branec" -f Dockerfile .; \
	fi

start-ide: runtime-image
	@mkdir -p "$(BRANE_NOTEBOOK_DIR)"
	@echo "Running JupyterLab to connect to Brane Instance @ $(BRANE_DRV)"
	DEBUG="$(DEBUG)" BRANE_API_URL="$(BRANE_API)" BRANE_DRV_URL="$(BRANE_DRV)" BRANE_NOTEBOOK_DIR="$(BRANE_NOTEBOOK_DIR)" docker-compose -p brane-ide -f docker-compose.yml up -d
	@chmod +x ./get_jupyterlab_token.sh
	@echo "JupyterLab launched at:"
	@echo "    $$(./get_jupyterlab_token.sh)"
	@echo ""
	@echo "Enter this link in your browser to connect to the server."

stop-ide:
	docker-compose -p brane-ide -f docker-compose.yml down

jupyterlab-token:
	@docker logs brane-ide 2>&1 \
	| grep "token=" \
	| tail -1 \
	| sed "s#.*token=##"
