CURRENT_SIGN_SETTING := $(shell git config commit.gpgSign)
.PHONY: clean-pyc clean-build docs

help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "test - run tests quickly with the default Python"
	@echo "dist - package"
	@echo "release - package and upload a release"
	@echo "docs - build and open documents"

clean: clean-build clean-pyc

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

test:
	pytest tests

build-docs:
	sphinx-apidoc -o docs/ asimov
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

docs: build-docs
	open docs/_build/html/index.html

linux-docs: build-docs
	xdg-open docs/_build/html/index.html

release: clean
	git config commit.gpgSign true
	bump2version $(bump)
	git push origin && git push origin --tags
	python setup.py sdist bdist_wheel
	twine upload --repository pypi dist/*
	git config commit.gpgSign "$(CURRENT_SIGN_SETTING)"

dist: clean
	python setup.py sdist bdist_wheel
	ls -l dist

code-cov:
	pytest --cov=asimov --cov-report=html tests/
	open htmlcov/index.html

lint:
	pylint asimov
