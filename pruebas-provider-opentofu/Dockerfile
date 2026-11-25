FROM golang:1.26-bookworm
# OpenTofu como binario suelto: es, literalmente, una de las cosas que enseña la serie.
RUN apt-get update -qq && apt-get install -y -qq curl unzip procps >/dev/null \
 && curl -fsSL -o /tmp/tofu.zip \
      https://github.com/opentofu/opentofu/releases/download/v1.12.6/tofu_1.12.6_linux_amd64.zip \
 && unzip -q /tmp/tofu.zip -d /tmp && mv /tmp/tofu /usr/local/bin/tofu \
 && chmod +x /usr/local/bin/tofu && rm -rf /tmp/* /var/lib/apt/lists/*
WORKDIR /lab
