# Execute a sequence of actions
all: install linting unittest

install:
	@echo "Install python modules local"
	python3.12 -m venv .venv
	. .venv/bin/activate; \
		pip install -r requirements.txt

linting:
	@echo "Check and fix liting locally"
	. .venv/bin/activate; \
		black ./src ./test --extend-exclude test/samples/; \
		isort ./src ./test --profile black --filter-files; \
		pylint ./src --fail-under=8 --disable=W1203

unittest:
	@echo "Check and fix liting locally"
	. .venv/bin/activate; \
		pytest --cov=./src -sv --cov-fail-under=10 --cov-report term-missing

run:
	. .venv/bin/activate; \
		python ./src/bot.py
