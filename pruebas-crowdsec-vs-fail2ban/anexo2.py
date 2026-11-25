# -*- coding: utf-8 -*-
"""Anexo 2 del SALIDA.md (2026-10-12): la trampa de instalar SOLO la colección sshd.
Quita crowdsecurity/linux (trae el parser base de syslog), reinicia, escribe 8 fallos y mira las métricas.
AÑADE la sección 9 al SALIDA.md.    python anexo2.py"""
import re
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def sh(c, timeout=120):
    r = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


def ex(*a):
    return sh(["docker", "exec", "anx2", *a])


sh(["docker", "rm", "-f", "anx2"])
sh(["docker", "run", "-d", "--name", "anx2", "--cap-add", "NET_ADMIN", "lab-cs"])
time.sleep(12)
quitar = ex("sh", "-c", "cscli collections remove crowdsecurity/linux --force 2>&1 | tail -3; "
                        "cscli parsers list 2>/dev/null | grep -c syslog-logs")
sh(["docker", "restart", "anx2"])
time.sleep(12)
ex("sh", "-c", "for i in 1 2 3 4 5 6 7 8; do echo \"$(date -u '+%b %e %H:%M:%S') servidor sshd[4501]: "
               "Failed password for root from 203.0.113.9 port 5000$i ssh2\" >> /var/log/auth.log; sleep 1; done")
time.sleep(4)
met = ex("sh", "-c", "cscli metrics show acquisition 2>/dev/null | grep -E 'Source|auth.log'; cscli decisions list 2>&1 | tail -1")
log = ex("sh", "-c", "grep -c -i error /var/log/crowdsec.log")
sh(["docker", "rm", "-f", "anx2"])
s = (AQUI / "SALIDA.md").read_text(encoding="utf-8")
s = re.sub(r"\n## 9 · Anexo.*", "", s, flags=re.S)
s += ("\n## 9 · Anexo: solo la colección sshd, sin la de linux\n\n### quitar crowdsecurity/linux\n\n"
      "`$ cscli collections remove crowdsecurity/linux --force; cscli parsers list | grep -c syslog-logs`\n\n```\n" + quitar
      + "\n```\n\n### 8 fallos después\n\n`$ cscli metrics show acquisition; cscli decisions list`\n\n```\n" + met
      + "\n```\n\n### errores en el registro\n\n`$ grep -c -i error /var/log/crowdsec.log`\n\n```\n" + log + "\n```\n")
(AQUI / "SALIDA.md").write_text(s, encoding="utf-8")
print(quitar, met, log, sep="\n---\n")
