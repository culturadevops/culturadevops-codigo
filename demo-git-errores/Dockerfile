# Imagen de las demos de git (cultura-devops, 2026-10-23): git + cliente y servidor OpenSSH.
# El «servidor» hace de GitHub en local (usuario git con git-shell y repos --bare); el «cliente» es tu máquina.
FROM debian:trixie-slim
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
      git openssh-client openssh-server ca-certificates procps less >/dev/null && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /run/sshd
