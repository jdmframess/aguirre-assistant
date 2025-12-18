FROM python:3.11-slim

WORKDIR /app
COPY ingestion/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ingestion ./ingestion
COPY common ./common
COPY data ./data
WORKDIR /app

CMD ["python", "ingestion/pipeline.py"]
