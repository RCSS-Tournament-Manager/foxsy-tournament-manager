FROM ghcr.io/astral-sh/uv:python3.12-bookworm

RUN apt update && \
    apt-get install -y fuse \
                       curl \
                       build-essential && \
    rm -rf /var/lib/apt/lists/*


RUN useradd -ms /bin/bash appuser

WORKDIR /app

# Install Dependencies
COPY [ "pyproject.toml",  "uv.lock", "/app/" ]
RUN uv sync

# Copy the application code
COPY . /app
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port and run the application
EXPOSE 8082

ENTRYPOINT ["/app/entrypoint.sh"]
