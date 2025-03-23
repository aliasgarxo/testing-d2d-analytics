# Use official Python image as base
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirement files
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY twitter_scraper.py twitter_scraper.py

# Set environment variables (optional, Kubernetes will override)
ENV TWITTER_API_KEY=""
ENV TWITTER_API_SECRET=""
ENV TWITTER_ACCESS_TOKEN=""
ENV TWITTER_ACCESS_SECRET=""
ENV DB_HOST="postgres-service"
ENV DB_PORT="5432"
ENV DB_NAME="tweetsdb"
ENV DB_USER="postgres"
ENV DB_PASSWORD="postgres"

# Command to run the script
CMD ["python", "twitter_scraper.py"]

