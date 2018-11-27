all: build open

build:
	docker build -t bigdata_networking .
run:
	docker run --name bigdata_networking --rm -v $(PWD)/datasets:/usr/src/app/datasets -it bigdata_networking
open:
	docker run --name bigdata_networking --rm -v $(PWD)/datasets:/usr/src/app/datasets --entrypoint "/bin/bash" -it bigdata_networking
