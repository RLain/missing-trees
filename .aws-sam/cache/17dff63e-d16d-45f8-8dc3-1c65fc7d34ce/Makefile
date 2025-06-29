build_sam:
	sam build --use-container --cached

start_api:
	sam local start-api --host 0.0.0.0 --port 3000

start_api_debug:
	sam local start-api --host 0.0.0.0 --port 3000 --debug



clean:
	find . -name "__pycache__" -exec rm -rf {} + -o -name "*.pyc" -delete
	rm -rf .aws-sam

lint:
	docker run --rm -v "${PWD}:/app" -w /app missing_trees flake8 src tests

test:
	docker run --rm -v $(shell pwd):/app -w /app -e PYTHONPATH=/app missing_trees pytest -v -s tests


# Archived:______________________
# build:
# 	docker build -t missing_trees .

# build_serverless:
# 	docker build -t my-serverless -f dockerfile.serverless .

# invoke_local:
# 	sam local invoke MissingTreesFunction --event events/test-event.json

# invoke_api:
# 	sls offline start

# run:
# 	docker run -it --rm -v "$$PWD":/app -w /app missing_trees bash

# run_handler:
# 	docker run --rm -v "$$PWD":/app -v "$$PWD/tmp":/tmp -w /app -e PYTHONPATH=/app missing_trees python src/api/handler.py

# run_serverless:
# 	docker run --rm --env-file .env -v "$(shell pwd):/app" -w /app my-serverless npx serverless deploy --stage staging --verbose