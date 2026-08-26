.PHONY: install run test lint

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

run:
	python3 main.py

test:
	pytest -v

lint:
	python3 -m py_compile main.py scraper/*.py
