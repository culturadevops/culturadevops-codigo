# Máquina de control del vídeo 800: aquí corren flota.py (asyncssh) y Ansible. Versiones fijas de Python.
FROM python:3.13.17-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssh-client \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir asyncssh==2.24.1 ansible-core==2.22.0
CMD ["sleep", "infinity"]
