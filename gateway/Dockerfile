FROM python:3.11-slim

WORKDIR /app

# Runtime deps
COPY gateway/requirements.txt ./gateway/requirements.txt
RUN pip install --no-cache-dir -r gateway/requirements.txt

# Copy scripts (EventStore, ConflictResolver, etc.) and gateway
COPY scripts/ ./scripts/
COPY gateway/ ./gateway/

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
