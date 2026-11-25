# -*- coding: utf-8 -*-
"""CrowdSec vs Fail2ban — banco de pruebas del vídeo 341 (cultura-devops, serie versus).

Dos servidores IDÉNTICOS (Debian bookworm + openssh + iptables), cada uno con su herramienta instalada como en un
servidor normal (paquetes de Debian / repo oficial de CrowdSec) y bloqueando con iptables:
  · srv-f2b  Fail2ban 1.0.2, jail sshd con los valores por defecto              10.79.0.11
  · srv-cs   CrowdSec + crowdsec-firewall-bouncer-iptables, colección sshd    10.79.0.12

Los intentos fallidos NO se generan contra sshd: el banco escribe en el auth.log de los dos servidores, a la vez y
al mismo ritmo, la línea que deja sshd cuando falla una contraseña («Failed password for root from <ip> …»). Así los
dos leen exactamente lo mismo. Lo que SÍ es real es el bloqueo: después se comprueba con una conexión TCP al
puerto 22 desde la IP baneada y desde una limpia.

Pruebas: 1) la trampa de las IP privadas; 2) ráfaga: 10 fallos, uno por segundo; 3) lento: uno cada 15 s;
4) el bloqueo de verdad; 5) quitar un baneo; 6) memoria e imagen.

    python correr.py
"""
import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
NET, SUB = "f2bcs", "10.79.0.0/24"
SRV = {"f2b": ("srv-f2b", "10.79.0.11", "lab-f2b"), "cs": ("srv-cs", "10.79.0.12", "lab-cs")}
salida = []


def sh(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def seccion(t):
    salida.extend(["", f"## {t}"])
    print(f"\n===== {t}", flush=True)


def ex(srv, *a, timeout=60):
    return sh(["docker", "exec", SRV[srv][0], *a], timeout=timeout)


def construir():
    for f, tag in (("Dockerfile.f2b", "lab-f2b"), ("Dockerfile.cs", "lab-cs"), ("Dockerfile.cliente", "lab-cliente")):
        sh(["docker", "build", "-q", "-t", tag, "-f", str(AQUI / "img" / f), str(AQUI / "img")], timeout=900)


def reset():
    sh(["docker", "rm", "-f", "srv-f2b", "srv-cs"])
    sh(["docker", "network", "rm", NET])
    sh(["docker", "network", "create", "--subnet", SUB, NET])


def arrancar():
    for k, (nombre, ip, img) in SRV.items():
        sh(["docker", "run", "-d", "--name", nombre, "--hostname", nombre, "--network", NET, "--ip", ip,
            "--cap-add", "NET_ADMIN", "--cap-add", "NET_RAW", img])
    t0 = time.time()
    while time.time() - t0 < 120:
        ok_f = "Number of jail" in ex("f2b", "fail2ban-client", "status")
        ok_c = "CROWDSEC_CHAIN" in ex("cs", "iptables", "-S")
        if ok_f and ok_c:
            break
        time.sleep(1)


def linea(ip, puerto):
    t = datetime.now(timezone.utc)
    return f"{t:%b} {t.day:>2} {t:%H:%M:%S} servidor sshd[{4000 + puerto % 900}]: Failed password for root from {ip} port {puerto} ssh2"


def escribir(ip, puerto):
    l = linea(ip, puerto)
    hilos = [threading.Thread(target=ex, args=(k, "sh", "-c", f"echo '{l}' >> /var/log/auth.log")) for k in SRV]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return l


def baneada(srv, ip):
    if srv == "f2b":
        return ip in ex("f2b", "fail2ban-client", "status", "sshd")
    try:
        return any(d.get("value") == ip for a in json.loads(ex("cs", "cscli", "decisions", "list", "-o", "json") or "[]") or []
                   for d in (a.get("decisions") or []))
    except Exception:
        return False


def ataque(ip, n, cada, titulo):
    """Escribe n fallos desde ip, uno cada `cada` segundos, y anota cuándo banea cada herramienta."""
    t0, ban, filas = time.time(), {"f2b": None, "cs": None}, []
    for i in range(1, n + 1):
        objetivo = t0 + (i - 1) * cada
        while time.time() < objetivo:
            for k in ban:
                if ban[k] is None and baneada(k, ip):
                    ban[k] = (time.time() - t0, i - 1)
            time.sleep(0.2)
        l = escribir(ip, 50000 + i)
        if i == 1:
            filas.append(f"línea escrita en los dos auth.log:\n  {l}\n")
        filas.append(f"{time.time() - t0:6.1f} s  fallo {i:2d}")
    fin = time.time() + max(cada, 15)
    while time.time() < fin and None in ban.values():
        for k in ban:
            if ban[k] is None and baneada(k, ip):
                ban[k] = (time.time() - t0, n)
        time.sleep(0.2)
    res = "\n".join(f"{nombre:9} " + (f"baneada a los {b[0]:.1f} s, tras {b[1]} fallos" if b else "NO la baneó")
                    for nombre, b in (("Fail2ban", ban["f2b"]), ("CrowdSec", ban["cs"])))
    anota(titulo, f"{n} fallos desde {ip}, uno cada {cada} s", "\n".join(filas[:1] + filas[1:4] + ["  …"] + filas[-2:]) + "\n\n" + res)
    return ban


def conecta(ip_cliente, srv):
    r = sh(["docker", "run", "--rm", "--network", NET, "--ip", ip_cliente, "lab-cliente", "sh", "-c",
            f"nc -z -w 3 {SRV[srv][1]} 22 && echo abierto || echo 'sin respuesta'"], timeout=60)
    return r.splitlines()[-1] if r else "?"


def main():
    construir()
    reset()
    arrancar()
    seccion("1 · Versiones y valores por defecto")
    anota("versiones", "fail2ban-server --version; crowdsec -version; crowdsec-firewall-bouncer -V",
          ex("f2b", "fail2ban-server", "--version").splitlines()[0] + "\n"
          + "crowdsec " + ex("cs", "sh", "-c", "crowdsec -version 2>&1 | sed -n 1p") + "\n"
          + "bouncer " + ex("cs", "sh", "-c", "crowdsec-firewall-bouncer -V 2>&1 | head -1"))
    anota("Fail2ban, jail sshd por defecto", "fail2ban-client get sshd maxretry|findtime|bantime; jail.conf ignoreip",
          "maxretry " + ex("f2b", "fail2ban-client", "get", "sshd", "maxretry") + "\n"
          + "findtime " + ex("f2b", "fail2ban-client", "get", "sshd", "findtime") + "\n"
          + "bantime  " + ex("f2b", "fail2ban-client", "get", "sshd", "bantime") + "\n"
          + ex("f2b", "sh", "-c", "grep -n '^#ignoreip' /etc/fail2ban/jail.conf"))
    anota("lo que hay que escribir para Fail2ban", "cat /etc/fail2ban/jail.d/lab.local",
          ex("f2b", "cat", "/etc/fail2ban/jail.d/lab.local"))
    anota("CrowdSec, escenarios de SSH por defecto", "grep capacity|leakspeed /etc/crowdsec/scenarios/ssh-*bf.yaml; profiles.yaml",
          ex("cs", "sh", "-c", "for f in ssh-bf ssh-slow-bf; do printf '%s: ' $f; grep -E '^(capacity|leakspeed):' "
                               "/etc/crowdsec/scenarios/$f.yaml | tr '\\n' ' '; echo; done; "
                               "grep -m1 duration /etc/crowdsec/profiles.yaml") + "\n"
          + ex("cs", "sh", "-c", "cscli scenarios list 2>/dev/null | grep -c 'crowdsecurity/ssh'") + " escenarios de SSH instalados")
    anota("lo que hay que escribir para CrowdSec", "cscli collections install crowdsecurity/linux crowdsecurity/sshd; cat acquis.d/ssh.yaml",
          ex("cs", "cat", "/etc/crowdsec/acquis.d/ssh.yaml") + "\n" + ex("cs", "sh", "-c", "cscli collections list 2>/dev/null | grep sshd"))
    anota("el bloqueador de CrowdSec ya está enganchado", "iptables -S | grep CROWDSEC; cscli bouncers list",
          ex("cs", "sh", "-c", "iptables -S | grep CROWDSEC") + "\n"
          + ex("cs", "sh", "-c", "cscli bouncers list -o json | grep -o '\"type\": *\"[^\"]*\"'"))

    seccion("2 · Una IP privada: ¿la banean?")
    ban = ataque("10.79.0.50", 10, 1, "ráfaga desde una IP privada (10.79.0.50)")
    anota("lo que leyó CrowdSec", "cscli metrics show acquisition",
          ex("cs", "sh", "-c", "cscli metrics show acquisition 2>/dev/null | grep -E 'Source|auth.log'"))
    if ban["cs"] is None:
        anota("las listas blancas instaladas", "cscli parsers list | grep -i whitelist",
              ex("cs", "sh", "-c", "cscli parsers list 2>/dev/null | grep -i -E 'whitelist|allowlist'"))
        anota("quitar la lista blanca (solo en el laboratorio)", "cscli parsers remove crowdsecurity/whitelists --force",
              ex("cs", "cscli", "parsers", "remove", "crowdsecurity/whitelists", "--force"))
        sh(["docker", "restart", "srv-cs"])
        t0 = time.time()
        while time.time() - t0 < 90 and "CROWDSEC_CHAIN" not in ex("cs", "iptables", "-S"):
            time.sleep(1)
        time.sleep(3)
    ex("f2b", "fail2ban-client", "unban", "--all")
    ex("cs", "cscli", "decisions", "delete", "--all")
    time.sleep(12)

    seccion("3 · Ráfaga: 10 fallos, uno por segundo")
    ataque("10.79.0.51", 10, 1, "ráfaga desde 10.79.0.51")
    time.sleep(3)
    anota("la decisión de CrowdSec", "cscli decisions list",
          ex("cs", "sh", "-c", "cscli decisions list 2>/dev/null | grep -E 'ID|10.79'"))
    anota("la de Fail2ban", "fail2ban-client status sshd", ex("f2b", "fail2ban-client", "status", "sshd"))

    seccion("4 · El bloqueo es real (conexión TCP al 22)")
    filas = []
    for k, nombre in (("f2b", "Fail2ban"), ("cs", "CrowdSec")):
        for ip in ("10.79.0.51", "10.79.0.60"):
            filas.append(f"{nombre:9} desde {ip} ({'baneada' if ip.endswith('51') else 'limpia '}): {conecta(ip, k)}")
    anota("nc -z al puerto 22", "nc -z -w 3 <servidor> 22", "\n".join(filas))
    anota("la regla en el cortafuegos", "iptables -S | grep 10.79.0.51; ipset",
          "Fail2ban: " + ex("f2b", "sh", "-c", "iptables -S | grep 10.79.0.51") + "\n"
          + "CrowdSec: " + ex("cs", "sh", "-c", "iptables -S | grep -i crowdsec | head -3; ipset list 2>/dev/null | grep -E '^Name|10.79.0.51' | head -4"))

    seccion("5 · Lento: un fallo cada 15 s")
    ataque("10.79.0.52", 18, 15, "lento desde 10.79.0.52")
    anota("qué escenario lo cazó en CrowdSec", "cscli alerts list",
          ex("cs", "sh", "-c", "cscli alerts list 2>/dev/null | grep -E 'ID|10.79'"))

    seccion("6 · Quitar un baneo")
    anota("Fail2ban", "fail2ban-client set sshd unbanip 10.79.0.51",
          ex("f2b", "fail2ban-client", "set", "sshd", "unbanip", "10.79.0.51"))
    anota("CrowdSec", "cscli decisions delete --ip 10.79.0.51",
          ex("cs", "cscli", "decisions", "delete", "--ip", "10.79.0.51"))
    time.sleep(12)
    anota("vuelve a entrar", "nc -z -w 3 <servidor> 22 desde 10.79.0.51",
          f"Fail2ban: {conecta('10.79.0.51', 'f2b')}\nCrowdSec: {conecta('10.79.0.51', 'cs')}")

    seccion("7 · Lo que pesa")
    anota("memoria (servidor con su herramienta, en reposo)", "docker stats --no-stream",
          sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}", "srv-f2b", "srv-cs"]))
    anota("procesos", "ps -o rss,comm",
          "Fail2ban:\n" + ex("f2b", "sh", "-c", "ps -eo rss,comm | grep -E 'fail2ban|sshd' | grep -v grep") + "\nCrowdSec:\n"
          + ex("cs", "sh", "-c", "ps -eo rss,comm | grep -E 'crowdsec|sshd' | grep -v grep"))
    anota("tamaño de la imagen (Debian + sshd + herramienta)", "docker image inspect -f {{.Size}}",
          "\n".join(f"{img:9} {int(sh(['docker', 'image', 'inspect', '-f', '{{.Size}}', img])) / 1e6:.1f} MB"
                    for img in ("lab-f2b", "lab-cs")))

    cab = ["# SALIDA — CrowdSec vs Fail2ban (vídeo 341)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. Los fallos se escriben en el "
           f"auth.log de los dos servidores a la vez (misma línea que deja sshd); el bloqueo se comprueba con una "
           f"conexión TCP real."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")
    print("SALIDA.md escrita")
    reset()
    sh(["docker", "network", "rm", NET])


if __name__ == "__main__":
    main()
