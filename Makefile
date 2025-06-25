build:
	docker build -t missing_trees .

run:
	docker run -it --rm -v "$$PWD":/app -w /app missing_trees bash

run-handler:
	docker run --rm -v "$$PWD":/app -w /app rebecca_lain_missing_trees bash -c "cd src && python handler.py"

test:
	docker run --rm -v "$$PWD":/app -w /app -e PYTHONPATH=/app missing_trees pytest src/tests
