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
	docker compose -f docker-compose.yml up -d

run_detached:
	docker compose -f docker-compose.yml up -d 

stop:
	docker compose down

test:
	docker run --rm -v $(shell pwd):/app -w /app -e PYTHONPATH=/app missing_trees pytest -v -s tests

shell:
	docker run --rm -it -v "${PWD}:/app" -w /app -e PYTHONPATH=/app missing_trees /bin/bash

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

deploy_image:
	@echo "Logging into ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	@echo "Tagging and pushing image..."
	docker tag missing_trees:latest $(ECR_REPO):latest
	docker push $(ECR_REPO):latest

deploy: build deploy-image
	@echo "Deploying to App Runner..."
	cd infrastructure && terraform apply -auto-approve
	@echo "Deployment complete!"
	cd infrastructure && terraform output app_runner_service_url

destroy:
	cd infrastructure && terraform destroy