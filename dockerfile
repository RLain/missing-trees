FROM python:3.11-slim

# Install Node.js & npm dependencies
RUN apt-get update && apt-get install -y curl gnupg \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g serverless \
  && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your app source
COPY . /app
WORKDIR /app