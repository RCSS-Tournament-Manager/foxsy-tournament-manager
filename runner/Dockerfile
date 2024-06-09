# Use an official Python runtime as a parent image
FROM python:3.9-slim

RUN apt update
RUN apt-get install -y fuse && rm -rf /var/lib/apt/lists/*

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
EXPOSE 8082

WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]