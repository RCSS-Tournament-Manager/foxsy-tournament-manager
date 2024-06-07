# Fake Storage

This is a fake storage implementation that can be used for testing purposes.

## Usage by docker file

### build the docker image

```bash
docker build -t app-storage .
```

### create logs directory and data directory
```bash
mkdir logs
mkdir data
```

### run the docker container
```bash
docker run -it --rm --name storage-container -p 80:80 -v ${PWD}/data:/app/data -v ${PWD}/logs:/app/logs -e API_KEY=secret app-storage
```
- it: interactive mode
- rm: remove the container after it stops
- name: name of the container
- p: port mapping (host_port:container_port)
- v: volume mapping (host_dir:container_dir)
- e: environment variable
- app-storage: image name