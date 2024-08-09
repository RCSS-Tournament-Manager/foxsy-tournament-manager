# Use an official Python runtime as a parent image
FROM python:3.9-slim

RUN apt update && apt-get install -y fuse curl build-essential && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

# Ensure Rust and Cargo are available in the environment for subsequent commands
ENV PATH="/root/.cargo/bin:${PATH}"

# Create a non-root user
RUN useradd -ms /bin/bash appuser

# Set the working directory and change ownership to the non-root user
WORKDIR /app
COPY . /app
RUN chown -R appuser:appuser /app

# Install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to the non-root user
USER appuser

# Expose port and run the application
EXPOSE 8085

WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]