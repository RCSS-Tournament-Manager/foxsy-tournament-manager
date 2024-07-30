# Docker Compose Example

## update .env file before running

### Build the Docker images, specifying the path to the .env file

```bash
docker-compose --env-file ../.env build
```

### Start the services, specifying the path to the .env file

```bash
docker-compose --env-file ../.env up
```

## minio

This directory contains a `docker-compose.yml` file that will start a minio server. 

Before Running, you need to create a directory and write absolute path to `docker-compose.yml` file.

```bash
docker-compose up
```

## rabbit

This directory contains a `docker-compose.yml` file that will start a rabbitmq server.

```bash
docker-compose up
```

## runner

This directory contains a `docker-compose.yml` file that will start a runner server.

Before Running, you need to create a directory and write absolute path to `docker-compose.yml` file.

```bash
docker-compose up
```

- if you want to use local image, you can change `image: naderzare/foxsy-runner-app:latest` to your image name in `docker-compose.yml` file.
- if you want to use local image (and build it first), you can change `image: naderzare/foxsy-runner-app:latest` to `build: ../../` in `docker-compose.yml` file.

## rabbit-minio-runner

This directory contains a `docker-compose.yml` file that will start a rabbitmq, minio and runner server.
