# -*- coding: utf-8 -*-
"""Anexo del SALIDA.md (2026-10-12): ¿con quién se conecta cada herramienta al arrancar?
Arranca un srv-cs y un srv-f2b limpios, espera 25 s y mira el registro de CrowdSec y las conexiones abiertas.
AÑADE la sección 8 al SALIDA.md.    python anexo.py"""
import re
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def sh(c, timeout=120):
    r = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


sh(["docker", "rm", "-f", "anx-cs", "anx-f2b"])
sh(["docker", "run", "-d", "--name", "anx-cs", "--cap-add", "NET_ADMIN", "lab-cs"])
sh(["docker", "run", "-d", "--name", "anx-f2b", "--cap-add", "NET_ADMIN", "lab-f2b"])
time.sleep(25)
cs = sh(["docker", "exec", "anx-cs", "sh", "-c",
         "grep -E 'Central API|community-blocklist|capi|enrolled' /var/log/crowdsec.log | sed 's/^time=\"[^\"]*\" //' | head -6"])
cred = sh(["docker", "exec", "anx-cs", "sh", "-c", "grep -o 'url: .*' /etc/crowdsec/online_api_credentials.yaml"])
f2b = sh(["docker", "exec", "anx-f2b", "sh", "-c", "grep -c -i -E 'http|api' /var/log/fail2ban.log 2>/dev/null; true"])
sh(["docker", "rm", "-f", "anx-cs", "anx-f2b"])
s = (AQUI / "SALIDA.md").read_text(encoding="utf-8")
s = re.sub(r"\n## 8 · Anexo.*", "", s, flags=re.S)
s += ("\n## 8 · Anexo: ¿con quién se conecta al arrancar?\n\n### CrowdSec: registro de arranque\n\n"
      "`$ grep -E 'Central API|community-blocklist' /var/log/crowdsec.log; online_api_credentials.yaml`\n\n```\n"
      + cs + "\n" + cred + "\n```\n\n### Fail2ban: líneas con http o api en su registro\n\n"
      "`$ grep -c -i -E 'http|api' /var/log/fail2ban.log`\n\n```\n" + f2b + "\n```\n")
(AQUI / "SALIDA.md").write_text(s, encoding="utf-8")
print(cs, cred, f2b, sep="\n")
