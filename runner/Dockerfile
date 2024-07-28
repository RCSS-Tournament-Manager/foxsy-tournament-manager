# Use an official Python runtime as a parent image
FROM python:3.12-bookworm

# Install required packages
RUN apt update && apt-get install -y fuse && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -ms /bin/bash appuser

# Set the working directory and change ownership to the non-root user
WORKDIR /home/appuser/app
COPY . /home/appuser/app
RUN chown -R appuser:appuser /home/appuser/app
RUN chmod -R 777 /home/appuser/app

# Create the necessary directories and set permissions
RUN mkdir -p /home/appuser/app/data /home/appuser/app/data/logs
RUN chown -R appuser:appuser /home/appuser/app/data /home/appuser/app/data/logs
RUN chmod -R 777 /home/appuser/app/data /home/appuser/app/data/logs

# Install dependencies
RUN pip install --no-cache-dir -r /home/appuser/app/requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /home/appuser/app/entrypoint.sh
RUN chmod +x /home/appuser/app/entrypoint.sh

# Switch to the non-root user
USER appuser

# Expose port and run the application
EXPOSE 8082

WORKDIR /home/appuser/app

ENTRYPOINT ["/home/appuser/app/entrypoint.sh"]
