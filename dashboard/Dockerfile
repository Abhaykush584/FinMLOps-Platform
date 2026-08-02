# File: dashboard/Dockerfile
# Build context: project root (d:\financial-pipeline-ml)
# docker build -f dashboard/Dockerfile -t streamlit-dashboard .

FROM python:3.12-slim

WORKDIR /app

# 1. Install Python dependencies
COPY dashboard/requirements.txt ./dashboard/requirements.txt
RUN pip install --no-cache-dir -r dashboard/requirements.txt

# 2. Copy dashboard source
COPY dashboard/ ./dashboard/

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit — server.address=0.0.0.0 required for Docker port binding
CMD ["streamlit", "run", "/app/dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
