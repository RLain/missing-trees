build:
	docker build -t missing_trees .

clean:
	find . -name "__pycache__" -exec rm -rf {} + -o -name "*.pyc" -delete

run:
	docker run -it --rm -v "$$PWD":/app -w /app missing_trees bash

run_handler:
	docker run --rm -v "$$PWD":/app -v "$$PWD/tmp":/tmp -w /app missing_trees bash -c "cd src && python handler.py"
	
test:
	docker run --rm -v $(shell pwd):/app -w /app -e PYTHONPATH=/app/src missing_trees pytest -v -s src/tests

