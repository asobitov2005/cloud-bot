SHELL := /bin/bash

.PHONY: install run migrate clean create-admin

install:
	python3 -m pip install -r requirements.txt

run:
	python3 main.py

migrate:
	python3 -m alembic upgrade head

migration:
	@read -p "Enter migration message: " msg; \
	python3 -m alembic revision --autogenerate -m "$$msg"

create-admin:
	@echo "Creating admin user..."
	@python3 create_admin.py admin admin

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
