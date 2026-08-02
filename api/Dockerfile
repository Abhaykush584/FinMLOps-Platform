# File: api/Dockerfile
# Build context: project root (d:\financial-pipeline-ml)
# docker build -f api/Dockerfile -t flask-api .

FROM python:3.12-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install Python dependencies (cached layer)
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# 2. Copy API source code
COPY api/ ./api/

# 3. Copy ML artifacts (will be overridden by volume mount in compose)
COPY ml/artifacts/ ./ml/artifacts/

# Expose Flask port
EXPOSE 5000

# Run Flask app directly via Python (no shell ambiguity)
CMD ["python", "/app/api/app.py"]