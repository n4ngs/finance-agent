FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Create data directory
RUN mkdir -p /home/railway/.personal-cfo

# Set environment
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/home/railway/.personal-cfo/finance.db
ENV PORT=5000

# Run the Flask API
CMD ["python3", "api.py"]
