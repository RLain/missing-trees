FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p temp
RUN python -c "import numpy; import scipy; import geopandas; import folium; print('Libraries preloaded')"

EXPOSE 8080

ENV PYTHONPATH=/app

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug", "--timeout", "120", "--preload"]
