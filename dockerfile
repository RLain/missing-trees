FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# {RL 02/07/25} Create temp directory for map files
RUN mkdir -p temp

EXPOSE 5000

ENV PYTHONPATH=/app

CMD ["python", "app.py"]