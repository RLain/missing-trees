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
	docker compose -f docker-compose.yml up

run_detached:
	docker compose -f docker-compose.yml up -d 

shell:
	docker run --rm -it -v "${PWD}:/app" -w /app -e PYTHONPATH=/app missing_trees /bin/bash

stop:
	docker compose down

test:
	docker run --rm -v $(shell pwd):/app -w /app -e PYTHONPATH=/app missing_trees pytest -v -s tests


# Deployment

AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)
AWS_REGION := af-south-1
ECR_REPO := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/missing-trees

terraform_init:
	cd infrastructure && terraform init

terraform_plan:
	cd infrastructure && terraform plan

terraform_apply:
	cd infrastructure && terraform apply

terraform_destroy:
	cd infrastructure && terraform destroy