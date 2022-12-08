# Read CLI first
ifdef DEBUG
DEBUG := 1
else
DEBUG := 0
endif

ifndef BRANEC
# Define the arguments for its version & architecture
ifndef VERSION
VERSION := 1.0.0
endif

ifndef ARCH
ARCH := x86_64
endif
endif

ifndef BRANE_API
# Remember, the kernel lives in a container so using localhost has no effect
BRANE_API := localhost:50051
endif

ifndef BRANE_DRV
# Remember, the kernel lives in a container so using localhost has no effect
BRANE_DRV := localhost:50053
endif

ifndef BRANE_NOTEBOOK_DIR
# Remember, the kernel lives in a container so using localhost has no effect
BRANE_NOTEBOOK_DIR := ./notebooks
endif


build-image:
	@if [[ -z "$(BRANEC)" ]]; then \
		echo "Building 'brane-ide' image with downloaded 'branec'..."; \
		docker build --load -t "brane-ide" --target brane-ide-download --build-arg "VERSION=$(VERSION)" --build-arg "ARCH=$(ARCH)" -f Dockerfile .; \
	else \
		echo "Building 'brane-ide' image with local 'branec'..."; \
		mkdir -p ".tmp"; \
		cp "$(BRANEC)" ".tmp/branec"; \
		docker build --load -t "brane-ide" --target brane-ide-local --build-arg "SOURCE=.tmp/branec" -f Dockerfile .; \
	fi

start-ide: build-image
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
