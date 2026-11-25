# Una máquina Debian con OpenSSH: hace de «instancia EC2» (usuario ubuntu, como en una AMI de Ubuntu) y de tu computadora.
FROM debian:trixie-slim
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends openssh-server openssh-client iptables procps curl jq ca-certificates >/dev/null     && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd     && useradd -m -s /bin/bash ubuntu && useradd -m -s /bin/bash ana     && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
CMD ["sleep", "infinity"]
