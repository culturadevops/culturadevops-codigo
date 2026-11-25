# Una máquina Debian con OpenSSH (servidor y cliente) y las herramientas para diagnosticar.
FROM debian:trixie-slim
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends openssh-server openssh-client netcat-openbsd iproute2 iptables procps >/dev/null \
    && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd \
    && useradd -m -s /bin/bash ana
CMD ["sleep", "infinity"]
