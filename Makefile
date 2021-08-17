.PHONY: install

install: install-kernels install-extensions

install-kernels: \
	install-bakery-kernel \
	install-bscript-kernel

install-bakery-kernel:
	pipenv shell "cd kernels/bakery && python setup.py install && exit" \
 && pipenv shell "cd kernels/bakery && python install.py --sys-prefix && exit"

install-bscript-kernel:
	pipenv shell "cd kernels/bscript && python setup.py install && exit" \
 && pipenv shell "cd kernels/bscript && python install.py --sys-prefix && exit"

install-extensions: install-js9 install-renderer

install-js9:
	pipenv run -- jupyter labextension install extensions/js9

install-registry:
	pipenv run -- jupyter labextension install extensions/registry

install-renderer:
	pipenv run -- jupyter labextension install extensions/renderer

clear:
	pipenv --rm

start:
	BRANE_DRV_URL="localhost:50053" pipenv run -- jupyter lab --ip 0.0.0.0 --LabApp.token=''

generate-grpc:
	pipenv run -- python -m grpc_tools.protoc --proto_path ./proto --python_out=. --grpc_python_out=. ./proto/driver.proto

start-ide:
	COMPOSE_IGNORE_ORPHANS=1 docker-compose -p brane -f docker-compose.yml up -d

stop-ide:
	COMPOSE_IGNORE_ORPHANS=1 docker-compose -p brane -f docker-compose.yml down

jupyterlab-token:
	@docker logs brane_brane-ide_1 2>&1 \
	| grep "token=" \
	| tail -1 \
	| sed "s#.*token=##"

