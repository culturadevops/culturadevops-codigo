#!/usr/bin/env bash
# Demo del vídeo 481 «¿Debo aprender Docker en la era de la IA?» — se EJECUTA y su salida va a SALIDA.md.
# Un Dockerfile típico de lo que genera una IA para una API pequeña en Python (funciona), contra uno revisado.
#   1) hadolint lo revisa sin construir;  2) se construyen los dos y se comparan tamaño y usuario;
#   3) trivy cuenta las vulnerabilidades altas y críticas de cada imagen.
# Todo en local; las imágenes se borran al final.
set -u
export MSYS_NO_PATHCONV=1
T=$(mktemp -d)
cd "$T"
mkdir -p ia revisado

cat > app.py <<'EOF'
from http.server import BaseHTTPRequestHandler, HTTPServer


class Hola(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"hola\n")


HTTPServer(("0.0.0.0", 8000), Hola).serve_forever()
EOF
echo "requests==2.32.5" > requirements.txt
cp app.py requirements.txt ia/
cp app.py requirements.txt revisado/

cat > ia/Dockerfile <<'EOF'
FROM python:latest
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y curl
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python app.py
EOF

cat > revisado/Dockerfile <<'EOF'
FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN useradd --uid 10001 --no-create-home app
USER app
EXPOSE 8000
CMD ["python", "app.py"]
EOF

echo '$ cat Dockerfile   # típico de lo que genera una IA'
cat ia/Dockerfile
echo
echo '$ hadolint Dockerfile'
docker run --rm -i hadolint/hadolint:v2.14.0 hadolint --no-color - < ia/Dockerfile 2>&1 | sed 's/^-:/Dockerfile:/'
echo
echo '$ hadolint Dockerfile   # versión revisada'
docker run --rm -i hadolint/hadolint:v2.14.0 hadolint --no-color - < revisado/Dockerfile 2>&1 | sed 's/^-:/Dockerfile:/'
echo "(código de salida: $(docker run --rm -i hadolint/hadolint:v2.14.0 hadolint --no-color - < revisado/Dockerfile >/dev/null 2>&1; echo $?))"
echo
docker build -q -t demo481-ia "$(cygpath -w "$T/ia")" >/dev/null 2>&1
docker build -q -t demo481-revisado "$(cygpath -w "$T/revisado")" >/dev/null 2>&1
echo '$ docker images --format "{{.Repository}} {{.Size}}"'
docker images --format "{{.Repository}} {{.Size}}" | grep demo481 | sed 's/demo481-ia/ia      /; s/demo481-revisado/revisado/'
echo '$ docker run --rm ia whoami && docker run --rm revisado whoami'
echo "ia:       $(docker run --rm --entrypoint whoami demo481-ia 2>&1)"
echo "revisado: $(docker run --rm --entrypoint whoami demo481-revisado 2>&1)"
echo
# solo los paquetes del sistema (Debian): ahí es donde la imagen base marca la diferencia
for i in ia revisado; do
  for extra in "" "--ignore-unfixed"; do
    echo "\$ trivy image --pkg-types os --severity HIGH,CRITICAL $extra $i" | tr -s ' '
    r=$(docker run --rm -v //var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache aquasec/trivy:0.67.2 image --quiet       --scanners vuln --pkg-types os --severity HIGH,CRITICAL $extra "demo481-$i" 2>&1 | grep -E "^Total:" | head -1)
    echo "${r:-Total: 0}"
  done
done
echo
echo '$ docker --version && trivy --version'
docker --version
docker run --rm aquasec/trivy:0.67.2 --version 2>&1 | head -1
docker run --rm hadolint/hadolint:v2.14.0 hadolint --version 2>&1 | head -1
docker rmi demo481-ia demo481-revisado >/dev/null 2>&1
cd / && rm -rf "$T"
