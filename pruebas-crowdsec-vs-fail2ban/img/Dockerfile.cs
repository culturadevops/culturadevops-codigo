FROM debian:bookworm-slim
RUN apt-get update -qq && apt-get install -y -qq curl gnupg openssh-server iptables >/dev/null \
 && curl -s https://install.crowdsec.net | sh >/dev/null \
 && (apt-get install -y -qq crowdsec crowdsec-firewall-bouncer-iptables >/dev/null 2>&1 || true) \
 && mkdir -p /run/sshd && touch /var/log/auth.log \
 && cscli hub update >/dev/null && cscli collections install crowdsecurity/linux crowdsecurity/sshd >/dev/null \
 && printf 'filenames:\n  - /var/log/auth.log\nlabels:\n  type: syslog\n' > /etc/crowdsec/acquis.d/ssh.yaml
COPY arranque-cs.sh /arranque-cs.sh
RUN chmod +x /arranque-cs.sh
CMD ["/arranque-cs.sh"]
