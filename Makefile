# Read CLI first
ifndef BRANE_INSTANCE
# Remember, the kernel lives in a container so using localhost has no effect
BRANE_INSTANCE := "brane-drv:50053"
endif

ifndef BRANE_NOTEBOOK_DIR
# Remember, the kernel lives in a container so using localhost has no effect
BRANE_NOTEBOOK_DIR := "./notebooks"
endif


.PHONY: install

install: install-packages install-kernels install-extensions

install-packages:
	pipenv install

install-kernels: \
	install-bakery-kernel \
	install-bscript-kernel

install-bakery-kernel:
	pipenv shell "cd kernels/bakery && python setup.py install && exit" \
 && pipenv shell "cd kernels/bakery && python install.py --sys-prefix && exit"

install-bscript-kernel:
	pipenv shell "cd kernels/bscript && python setup.py install && exit" \
 && pipenv shell "cd kernels/bscript && python install.py --sys-prefix && exit"

# install-extensions: install-manager install-js9 install-renderer
install-extensions: install-js9 install-renderer

# install-manager:
# 	pipenv run -- jupyter labextension install "@jupyter-widgets/jupyterlab-manager"

install-js9:
	pipenv run -- jupyter labextension install extensions/js9

install-registry:
	pipenv run -- jupyter labextension install extensions/registry

install-renderer:
	pipenv run -- jupyter labextension install extensions/renderer

clear:
	pipenv --rm

generate-grpc:
	pipenv run -- python -m grpc_tools.protoc --proto_path ./proto --python_out=. --grpc_python_out=. ./proto/driver.proto

build-image:
	docker build --load -t "brane-ide" -f Dockerfile .

start-ide: build-image
	@mkdir -p "$(BRANE_NOTEBOOK_DIR)"
	@echo "Running JupyterLab to connect to Brane Instance @ $(BRANE_INSTANCE)"
	BRANE_DRV_URL="$(BRANE_INSTANCE)" BRANE_NOTEBOOK_DIR="$(BRANE_NOTEBOOK_DIR)" COMPOSE_IGNORE_ORPHANS=1 docker-compose -p brane-ide -f docker-compose.yml up -d
	@chmod +x ./get_jupyterlab_token.sh
	@echo "JupyterLab launched at:"
	@echo "    $$(./get_jupyterlab_token.sh)"
	@echo ""
	@echo "Enter this link in your browser to connect to the server."

stop-ide:
	COMPOSE_IGNORE_ORPHANS=1 docker-compose -p brane-ide -f docker-compose.yml down

jupyterlab-token:
	@docker logs brane-ide 2>&1 \
	| grep "token=" \
	| tail -1 \
	| sed "s#.*token=##"

