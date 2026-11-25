$ cat Dockerfile   # típico de lo que genera una IA
FROM python:latest
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y curl
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python app.py

$ hadolint Dockerfile
Dockerfile:1 DL3007 warning: Using latest is prone to errors if the image will ever update. Pin the version explicitly to a release tag
Dockerfile:4 DL3008 warning: Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install <package>=<version>`
Dockerfile:4 DL3015 info: Avoid additional packages by specifying `--no-install-recommends`
Dockerfile:4 DL3009 info: Delete the apt lists (/var/lib/apt/lists) after installing something
Dockerfile:5 DL3042 warning: Avoid use of cache directory with pip. Use `pip install --no-cache-dir <package>`
Dockerfile:7 DL3025 warning: Use arguments JSON notation for CMD and ENTRYPOINT arguments

$ hadolint Dockerfile   # versión revisada
(código de salida: 0)

$ docker images --format "{{.Repository}} {{.Size}}"
revisado 194MB
ia       1.7GB
$ docker run --rm ia whoami && docker run --rm revisado whoami
ia:       root
revisado: app

$ trivy image --pkg-types os --severity HIGH,CRITICAL ia
Total: 321 (HIGH: 305, CRITICAL: 16)
$ trivy image --pkg-types os --severity HIGH,CRITICAL --ignore-unfixed ia
Total: 4 (HIGH: 4, CRITICAL: 0)
$ trivy image --pkg-types os --severity HIGH,CRITICAL revisado
Total: 44 (HIGH: 44, CRITICAL: 0)
$ trivy image --pkg-types os --severity HIGH,CRITICAL --ignore-unfixed revisado
Total: 0

$ docker --version && trivy --version
Docker version 29.6.2, build dfc4efb
Version: 0.67.2
Haskell Dockerfile Linter 2.14.0
