FROM ghcr.io/astral-sh/uv:python3.12-bookworm

RUN apt update && \
    apt-get install -y fuse \
                       curl \
                       build-essential && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Install Dependencies
COPY [ "pyproject.toml",  "uv.lock", "/app/" ]
RUN uv sync

# Copy the application code
COPY . /app

# Expose port and run the application
EXPOSE 8082

ENTRYPOINT ["/app/entrypoint.sh"]
