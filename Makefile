build:
	docker build -t missing_trees .

clean:
	@echo "Removing .pycaches..."
	find . -name "__pycache__" -exec rm -rf {} + -o -name "*.pyc" -delete
	@echo "Removing temp files..."
	rm -rf temp/

lint:
	docker run --rm -v "${PWD}:/app" -w /app missing_trees flake8 src tests

run:
	docker run --rm -p 3000:5000 -v "${PWD}:/app" -w /app \
		-e FLASK_ENV=development \
		-e PYTHONPATH=/app \
		missing_trees python src/app.py

run_detached:
	docker run -d --name missing_trees_api -p 3000:5000 -v "${PWD}:/app" -w /app \
		-e FLASK_ENV=development \
		-e PYTHONPATH=/app \
		missing_trees python src/app.py

stop:
	docker stop missing_trees && docker rm missing_trees

test:
	docker run --rm -v $(shell pwd):/app -w /app -e PYTHONPATH=/app missing_trees pytest -v -s tests

shell:
	docker run --rm -it -v "${PWD}:/app" -w /app -e PYTHONPATH=/app missing_trees /bin/bash