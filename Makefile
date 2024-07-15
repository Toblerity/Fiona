PYTHON_VERSION ?= 3.10
GDAL ?= ubuntu-small-3.9.0
all: deps clean install test

.PHONY: docs

install:
	python setup.py build_ext
	pip install -e .[all]

deps:
	pip install -r requirements-dev.txt

clean:
	pip uninstall -y fiona || echo "no need to uninstall"
	python setup.py clean --all
	find . -name '__pycache__' -delete -print -o -name '*.pyc' -delete -print
	touch fiona/*.pyx

sdist:
	python setup.py sdist

test:
	python -m pytest --maxfail 1 -v --cov fiona --cov-report html --pdb tests

docs:
	cd docs && make apidocs && make html

doctest:
	py.test --doctest-modules fiona --doctest-glob='*.rst' docs/*.rst

dockertestimage:
	docker build --target gdal --build-arg GDAL=$(GDAL) --build-arg PYTHON_VERSION=$(PYTHON_VERSION) -t fiona:$(GDAL)-py$(PYTHON_VERSION) .

dockertest: dockertestimage
	docker run -it -v $(shell pwd):/app -v /tmp:/tmp --env AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY --entrypoint=/bin/bash fiona:$(GDAL)-py$(PYTHON_VERSION) -c '/venv/bin/python -m pip install -vvv --editable .[all] --no-build-isolation && /venv/bin/python -B -m pytest -m "not wheel" --cov fiona --cov-report term-missing $(OPTS)'

dockershell: dockertestimage
	docker run -it -v $(shell pwd):/app --env AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY --entrypoint=/bin/bash fiona:$(GDAL)-py$(PYTHON_VERSION) -c '/venv/bin/python -m pip install --editable . --no-build-isolation && /bin/bash'

dockersdist: dockertestimage
	docker run -it -v $(shell pwd):/app --env AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY --entrypoint=/bin/bash fiona:$(GDAL)-py$(PYTHON_VERSION) -c '/venv/bin/python -m build --sdist'

dockergdb: dockertestimage
	docker run -it -v $(shell pwd):/app --env AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY --entrypoint=/bin/bash fiona:$(GDAL)-py$(PYTHON_VERSION) -c '/venv/bin/python -m pip install --editable . --no-build-isolation && gdb -ex=r --args /venv/bin/python -B -m pytest -m "not wheel" --cov fiona --cov-report term-missing $(OPTS)'

dockerdocs: dockertestimage
	docker run -it -v $(shell pwd):/app --entrypoint=/bin/bash fiona:$(GDAL)-py$(PYTHON_VERSION) -c 'source /venv/bin/activate && cd docs && make clean && make html'

dockertestimage-amd64:
	docker build --platform linux/amd64 --target gdal --build-arg GDAL=$(GDAL) --build-arg PYTHON_VERSION=$(PYTHON_VERSION) -t fiona-amd64:$(GDAL)-py$(PYTHON_VERSION) .

dockertest-amd64: dockertestimage-amd64
	docker run -it -v $(shell pwd):/app -v /tmp:/tmp --env AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY --entrypoint=/bin/bash fiona-amd64:$(GDAL)-py$(PYTHON_VERSION) -c '/venv/bin/python -m pip install tiledb && /venv/bin/python -m pip install --editable .[all] --no-build-isolation && /venv/bin/python -B -m pytest -m "not wheel" --cov fiona --cov-report term-missing $(OPTS)'
