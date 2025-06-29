build:
	docker build -t missing_trees .

clean:
	find . -name "__pycache__" -exec rm -rf {} + -o -name "*.pyc" -delete

lint:
	docker run --rm -v "${PWD}:/app" -w /app missing_trees flake8 src tests

run:
	docker run -it --rm -v "$$PWD":/app -w /app missing_trees bash

run_handler:
	docker run --rm -v "$$PWD":/app -v "$$PWD/tmp":/tmp -w /app -e PYTHONPATH=/app missing_trees python src/api/handler.py
	
test:
	docker run --rm -v $(shell pwd):/app -w /app -e PYTHONPATH=/app missing_trees pytest -v -s tests

