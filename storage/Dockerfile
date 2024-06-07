# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Create a non-root user
RUN useradd -ms /bin/bash appuser

# Set the working directory and change ownership to the non-root user
WORKDIR /app
COPY . /app
RUN chown -R appuser:appuser /app

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to the non-root user
USER appuser

# Expose port and run the application
EXPOSE 80

WORKDIR /app
#CMD ["python", "-m", "main", "--data-dir", "/app/data", "--log-dir", "/app/logs", "--port", "80", "--api-key-name", "${API_KEY_NAME:-api-key-name}", "--api-key", "${API_KEY:-api-key}"]
ENTRYPOINT ["/app/entrypoint.sh"]