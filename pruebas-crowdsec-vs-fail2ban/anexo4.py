# -*- coding: utf-8 -*-
"""Anexo 4 del SALIDA.md (2026-10-12): Fail2ban con lo que trae Debian 12 y sin /var/log/auth.log (Debian 12 no
instala rsyslog: SSH escribe en el journal). AÑADE la sección 11.    python anexo4.py"""
import re
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def sh(c, timeout=120):
    r = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


rsys = sh(["docker", "run", "--rm", "debian:bookworm-slim", "sh", "-c", "dpkg -l rsyslog 2>&1 | tail -1"])
deb = sh(["docker", "run", "--rm", "lab-f2b", "cat", "/etc/fail2ban/jail.d/defaults-debian.conf"])
arranque = sh(["docker", "run", "--rm", "--cap-add", "NET_ADMIN", "lab-f2b", "sh", "-c",
               "rm -f /etc/fail2ban/jail.d/lab.local /var/log/auth.log; mkdir -p /run/fail2ban; "
               "fail2ban-server -xf start > /tmp/f2b.out 2>&1 & sleep 6; "
               "grep -i -E 'have not|failed during' /tmp/f2b.out | sed 's/^[0-9-]* [0-9:,]* //' | head -2"], timeout=60)
s = (AQUI / "SALIDA.md").read_text(encoding="utf-8")
s = re.sub(r"\n## 11 · Anexo.*", "", s, flags=re.S)
s += ("\n## 11 · Anexo: Fail2ban en un Debian 12 recién instalado\n\n### ¿hay rsyslog?\n\n`$ dpkg -l rsyslog`\n\n```\n"
      + rsys + "\n```\n\n### lo que activa el paquete de Debian\n\n`$ cat /etc/fail2ban/jail.d/defaults-debian.conf`\n\n```\n"
      + deb + "\n```\n\n### arrancar así, sin auth.log\n\n`$ fail2ban-server -xf start`\n\n```\n" + arranque + "\n```\n")
(AQUI / "SALIDA.md").write_text(s, encoding="utf-8")
print(rsys, deb, arranque, sep="\n---\n")
