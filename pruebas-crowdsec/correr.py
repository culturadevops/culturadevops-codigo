# -*- coding: utf-8 -*-
"""CrowdSec — banco de pruebas del vídeo 327 (cultura-devops, serie herramientas).

Red Docker `cs` con:
  · sshd     Debian + openssh + rsyslog → /logs/auth.log (volumen compartido)
  · web      crowdsecurity/openresty: nginx con el bouncer de CrowdSec dentro
  · crowdsec lee auth.log (syslog) y los logs del contenedor web (fuente docker)
  · atacante-ssh y atacante-web, cada uno con su IP fija
Todo a SALIDA.md.

    python correr.py
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CS = "crowdsecurity/crowdsec:latest"
WEB = "crowdsecurity/openresty:latest"
KEY = "clave-del-bouncer-de-prueba-1234567890"
salida = []

ACQUIS = """filenames:
  - /logs/auth.log
labels:
  type: syslog
---
source: docker
container_name:
  - web
labels:
  type: nginx
"""

SSHD = """FROM debian:bookworm-slim
RUN apt-get update -qq && apt-get install -y -qq openssh-server rsyslog >/dev/null \\
 && mkdir -p /run/sshd && echo 'root:la-de-verdad-es-otra' | chpasswd \\
 && sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \\
 && sed -i '/imklog/d' /etc/rsyslog.conf \\
 && echo 'auth,authpriv.* /logs/auth.log' > /etc/rsyslog.d/50-auth.conf
CMD rsyslogd && /usr/sbin/sshd -D
"""

ATACANTE = """FROM debian:bookworm-slim
RUN apt-get update -qq && apt-get install -y -qq sshpass openssh-client curl >/dev/null
"""


def sh(cmd, timeout=900, entrada=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, input=entrada)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1200]}\n", flush=True)


def cscli(*a):
    return sh(["docker", "exec", "crowdsec", "cscli", *a])


def main():
    (AQUI / "acquis.yaml").write_text(ACQUIS, encoding="utf-8")
    print(sh(["docker", "build", "-q", "-t", "cs-sshd", "-"], entrada=SSHD))
    print(sh(["docker", "build", "-q", "-t", "cs-atacante", "-"], entrada=ATACANTE))
    sh(["docker", "rm", "-f", "crowdsec", "web", "sshd"])
    sh(["docker", "volume", "rm", "-f", "cs-logs", "cs-data"])
    sh(["docker", "network", "rm", "cs"])
    sh(["docker", "network", "create", "--subnet", "10.77.0.0/24", "cs"])

    salida.append("\n## 1 · Levantar el laboratorio")
    sh(["docker", "run", "-d", "--name", "sshd", "--network", "cs", "--ip", "10.77.0.10",
        "-v", "cs-logs:/logs", "cs-sshd"])
    t0 = time.time()
    sh(["docker", "run", "-d", "--name", "crowdsec", "--network", "cs", "--ip", "10.77.0.2",
        "-e", "COLLECTIONS=crowdsecurity/sshd crowdsecurity/nginx",
        "-e", f"BOUNCER_KEY_web={KEY}",
        "-v", "cs-data:/var/lib/crowdsec/data",
        "-v", "cs-logs:/logs:ro", "-v", f"{AQUI / 'acquis.yaml'}:/etc/crowdsec/acquis.yaml:ro",
        "-v", "//var/run/docker.sock:/var/run/docker.sock:ro", CS])
    for _ in range(120):
        if "200" in sh(["docker", "exec", "crowdsec", "sh", "-c",
                        "wget -qS -O- http://127.0.0.1:8080/health 2>&1 | head -1"]):
            break
        time.sleep(1)
    anota("arranque de crowdsec", "docker run -d --name crowdsec ... crowdsecurity/crowdsec",
          f"listo en {time.time() - t0:.0f} s\n" + cscli("version").split("\n")[0])
    sh(["docker", "run", "-d", "--name", "web", "--network", "cs", "--ip", "10.77.0.20",
        "-e", "API_URL=http://10.77.0.2:8080", "-e", f"API_KEY={KEY}",
        "-e", "UPDATE_FREQUENCY=5", WEB])
    time.sleep(8)

    salida.append("\n## 2 · Lo que lee y lo que sabe detectar")
    anota("versión", "cscli version", cscli("version"))
    anota("colecciones", "cscli collections list", cscli("collections", "list"))
    anota("escenarios", "cscli scenarios list", cscli("scenarios", "list"))
    anota("bouncers", "cscli bouncers list", cscli("bouncers", "list"))

    salida.append("\n## 3 · La web responde a todo el mundo")
    for ip in ("10.77.0.50", "10.77.0.60"):
        anota(f"curl desde {ip}", "curl -s -o /dev/null -w '%{http_code}' http://web/",
              sh(["docker", "run", "--rm", "--network", "cs", "--ip", ip, "cs-atacante",
                  "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://web/"]))

    salida.append("\n## 4 · Ataque de fuerza bruta por SSH (desde 10.77.0.50)")
    script = ("for p in 123456 password admin root qwerty letmein 111111 dragon; do "
              "t=$(date +%T); sshpass -p $p ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
              "root@sshd true 2>/dev/null; echo \"$t  intento $p -> $?\"; done")
    anota("8 contraseñas", "for p in ...; do sshpass -p $p ssh root@sshd true; done",
          sh(["docker", "run", "--rm", "--network", "cs", "--ip", "10.77.0.50", "cs-atacante",
              "sh", "-c", script], timeout=300))
    anota("lo que quedó en auth.log", "grep 'Failed password' /logs/auth.log | tail -3",
          sh(["docker", "exec", "sshd", "sh", "-c",
              "grep -c 'Failed password' /logs/auth.log; grep 'Failed password' /logs/auth.log | tail -3"]))
    time.sleep(5)
    anota("alertas", "cscli alerts list", cscli("alerts", "list"))
    anota("decisiones", "cscli decisions list", cscli("decisions", "list"))

    salida.append("\n## 4b · La trampa: las IP privadas están en lista blanca")
    anota("métricas de lectura", "cscli metrics show acquisition",
          cscli("metrics", "show", "acquisition"))
    anota("la lista blanca por defecto", "cat .../parsers/s02-enrich/whitelists.yaml",
          sh(["docker", "exec", "crowdsec", "sh", "-c",
              "cat /etc/crowdsec/parsers/s02-enrich/whitelists.yaml"]))
    anota("quitarla (solo en el laboratorio)", "cscli parsers remove crowdsecurity/whitelists --force",
          cscli("parsers", "remove", "crowdsecurity/whitelists", "--force"))
    sh(["docker", "restart", "crowdsec"])
    for _ in range(60):
        if "200" in sh(["docker", "exec", "crowdsec", "sh", "-c",
                        "wget -qS -O- http://127.0.0.1:8080/health 2>&1 | head -1"]):
            break
        time.sleep(1)
    time.sleep(3)
    anota("el mismo ataque otra vez", "for p in ...; do sshpass -p $p ssh root@sshd true; done",
          sh(["docker", "run", "--rm", "--network", "cs", "--ip", "10.77.0.50", "cs-atacante",
              "sh", "-c", script], timeout=300))
    time.sleep(5)
    anota("alertas", "cscli alerts list", cscli("alerts", "list"))
    anota("decisiones", "cscli decisions list", cscli("decisions", "list"))
    anota("y por SSH, ¿ya no entra?", "ssh root@sshd (con la contraseña buena)",
          sh(["docker", "run", "--rm", "--network", "cs", "--ip", "10.77.0.50", "cs-atacante",
              "sh", "-c", "sshpass -p la-de-verdad-es-otra ssh -o StrictHostKeyChecking=no "
                          "root@sshd 'echo dentro'; echo codigo=$?"], timeout=120))

    salida.append("\n## 5 · El bloqueo: la IP baneada tampoco ve la web")
    time.sleep(8)
    for ip in ("10.77.0.50", "10.77.0.60"):
        anota(f"curl desde {ip}", "curl -s -o /dev/null -w '%{http_code}' http://web/",
              sh(["docker", "run", "--rm", "--network", "cs", "--ip", ip, "cs-atacante",
                  "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://web/"]))

    salida.append("\n## 6 · Escaneo de la web (desde 10.77.0.60)")
    rutas = ("/.env /.git/config /wp-login.php /admin /phpmyadmin/ /backup.zip /config.php "
             "/.aws/credentials /server-status /wp-config.php.bak /db.sql /.htpasswd")
    script = (f"for r in {rutas}; do printf '%s %s\\n' $(curl -s -o /dev/null -w '%{{http_code}}' "
              "http://web$r) $r; done")
    anota("12 rutas sensibles", "for r in /.env /.git/config ...; do curl http://web$r; done",
          sh(["docker", "run", "--rm", "--network", "cs", "--ip", "10.77.0.60", "cs-atacante",
              "sh", "-c", script], timeout=300))
    time.sleep(6)
    anota("alertas", "cscli alerts list", cscli("alerts", "list"))
    anota("decisiones", "cscli decisions list", cscli("decisions", "list"))
    time.sleep(8)
    anota("y ahora la web, desde 10.77.0.60", "curl -s -o /dev/null -w '%{http_code}' http://web/",
          sh(["docker", "run", "--rm", "--network", "cs", "--ip", "10.77.0.60", "cs-atacante",
              "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://web/"]))
    anota("una IP limpia sigue entrando", "curl desde 10.77.0.70",
          sh(["docker", "run", "--rm", "--network", "cs", "--ip", "10.77.0.70", "cs-atacante",
              "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://web/"]))

    salida.append("\n## 7 · Quitar un baneo y métricas")
    anota("desbanear", "cscli decisions delete --ip 10.77.0.50", cscli("decisions", "delete", "--ip", "10.77.0.50"))
    time.sleep(8)
    anota("vuelve a entrar", "curl desde 10.77.0.50",
          sh(["docker", "run", "--rm", "--network", "cs", "--ip", "10.77.0.50", "cs-atacante",
              "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://web/"]))
    anota("métricas de lectura", "cscli metrics show acquisition parsers",
          cscli("metrics", "show", "acquisition", "parsers"))
    anota("memoria", "docker stats --no-stream crowdsec web",
          sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}", "crowdsec", "web"]))

    sh(["docker", "rm", "-f", "crowdsec", "web", "sshd"])
    sh(["docker", "volume", "rm", "-f", "cs-logs", "cs-data"])
    sh(["docker", "network", "rm", "cs"])
    cab = ["# SALIDA — CrowdSec (vídeo 327)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Imágenes {CS} y {WEB}."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
