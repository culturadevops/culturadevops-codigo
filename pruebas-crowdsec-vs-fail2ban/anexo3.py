# -*- coding: utf-8 -*-
"""Anexo 3 del SALIDA.md (2026-10-12): lo que trae cada uno para otros servicios, la reincidencia y la lista blanca.
AÑADE la sección 10 al SALIDA.md.    python anexo3.py"""
import re
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def sh(c, timeout=120):
    r = subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


sh(["docker", "rm", "-f", "anx3-cs", "anx3-f2b"])
sh(["docker", "run", "-d", "--name", "anx3-cs", "--cap-add", "NET_ADMIN", "lab-cs"])
sh(["docker", "run", "-d", "--name", "anx3-f2b", "--cap-add", "NET_ADMIN", "lab-f2b"])
time.sleep(15)
bloques = [
    ("Fail2ban: cárceles y filtros que trae", "grep -c '^\[' jail.conf; ls filter.d | wc -l",
     sh(["docker", "exec", "anx3-f2b", "sh", "-c",
         "echo cárceles: $(grep -cE '^\[[a-z0-9-]+\]' /etc/fail2ban/jail.conf); echo filtros: $(ls /etc/fail2ban/filter.d/*.conf | wc -l)"])),
    ("Fail2ban: la cárcel de reincidentes", "grep -A12 '^\[recidive\]' jail.conf",
     sh(["docker", "exec", "anx3-f2b", "sh", "-c", "grep -A14 '^\[recidive\]' /etc/fail2ban/jail.conf | grep -E '^\[|^bantime|^findtime|^maxretry|^logpath'"])),
    ("Fail2ban: tu propia IP fuera", "grep ignoreip jail.conf",
     sh(["docker", "exec", "anx3-f2b", "sh", "-c", "grep -n 'ignoreip' /etc/fail2ban/jail.conf | head -2"])),
    ("CrowdSec: colecciones disponibles en su hub", "cscli collections list -a | grep -c crowdsecurity/",
     sh(["docker", "exec", "anx3-cs", "sh", "-c", "echo colecciones: $(cscli collections list -a 2>/dev/null | grep -c 'crowdsecurity/'); echo escenarios: $(cscli scenarios list -a 2>/dev/null | grep -c 'crowdsecurity/')"])),
    ("CrowdSec: bloqueos más largos para quien repite", "grep duration profiles.yaml",
     sh(["docker", "exec", "anx3-cs", "sh", "-c", "grep -n -m2 'duration' /etc/crowdsec/profiles.yaml"])),
    ("CrowdSec: tu propia IP fuera", "cscli allowlists create casa; cscli allowlists add casa 198.51.100.7; cscli allowlists list",
     sh(["docker", "exec", "anx3-cs", "sh", "-c", "cscli allowlists create casa -d 'mi IP' 2>&1 | tail -1; "
                                                   "cscli allowlists add casa 198.51.100.7 2>&1 | tail -1; cscli allowlists list 2>&1 | grep -E 'Name|casa'"])),
]
sh(["docker", "rm", "-f", "anx3-cs", "anx3-f2b"])
s = (AQUI / "SALIDA.md").read_text(encoding="utf-8")
s = re.sub(r"\n## 10 · Anexo.*", "", s, flags=re.S)
s += "\n## 10 · Anexo: otros servicios, reincidencia y tu propia IP\n"
for t, c, o in bloques:
    s += f"\n### {t}\n\n`$ {c}`\n\n```\n{o}\n```\n"
    print(f"--- {t}\n{o}\n")
(AQUI / "SALIDA.md").write_text(s, encoding="utf-8")
