FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY . .

# No external dependencies needed for Phase 1
# If Plaid is added later, uncomment:
# RUN pip install -r requirements.txt

# Create data directory
RUN mkdir -p /home/railway/.personal-cfo

# Set environment
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/home/railway/.personal-cfo/finance.db

# Run the application
CMD ["python3", "main.py"]
