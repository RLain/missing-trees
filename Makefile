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
	docker run --rm -p 3000:8080 -v "${PWD}:/app" -w /app \
		-e FLASK_ENV=development \
		-e PYTHONPATH=/app \
		missing_trees python src/app.py

run_detached:
	docker run -d --name missing_trees -p 3000:8080 -v "${PWD}:/app" -w /app \
		-e FLASK_ENV=development \
		-e PYTHONPATH=/app \
		missing_trees python src/app.py

stop:
	docker stop missing_trees && docker rm missing_trees

test:
	docker run --rm -v $(shell pwd):/app -w /app -e PYTHONPATH=/app missing_trees pytest -v -s tests

shell:
	docker run --rm -it -v "${PWD}:/app" -w /app -e PYTHONPATH=/app missing_trees /bin/bash

# Deployment

# Add these variables at the top
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)
AWS_REGION := af-south-1
ECR_REPO := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/missing-trees

# Add these new targets
terraform-init:
	cd infrastructure && terraform init

terraform-plan:
	cd infrastructure && terraform plan

terraform-apply:
	cd infrastructure && terraform apply

deploy-image:
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