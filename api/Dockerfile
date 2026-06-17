FROM python:3.11-slim
WORKDIR /opt/app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ api/
COPY ml/model.pkl ml/model.pkl
RUN mkdir -p data && curl -L \
    https://github.com/zaheerqur/nyc-taxi-platform/releases/download/v1.0-data/nyc_taxi.duckdb \
    -o data/nyc_taxi.duckdb
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
