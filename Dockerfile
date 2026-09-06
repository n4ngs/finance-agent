FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# NOTE: DATABASE_PATH is set via Railway's persistent Volume mounted at
# /data (see: railway volume add --mount-path /data). Without a Volume,
# anything written here is wiped on every redeploy. DATABASE_PATH is
# configured as a Railway environment variable, not hardcoded here.
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Run the Flask API
CMD ["python3", "api.py"]
