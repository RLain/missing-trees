FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
# {RL 03/07/2025} Installs gcc, a C compiler, required for building Python packages with native extensions (geopandas/numpy etc)
    gcc \ 
    # {RL 03/07/2025} cleans up cache after install to keep the image small.
    && rm -rf /var/lib/apt/lists/* 

COPY requirements.txt .
# {RL 03/07/2025} --no-cache-dir Installs Python dependencies without caching to reduce image size.
RUN pip install --no-cache-dir -r requirements.txt 

RUN mkdir -p temp

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.app:app"]