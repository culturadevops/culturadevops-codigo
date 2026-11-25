# -*- coding: utf-8 -*-
"""Demo del vídeo 800 de cultura-devops, «Un comando en 50 servidores por SSH: Python o Ansible».
Laboratorio copiado del 682 de golandia (cliente SSH en Go): 50 servidores sshd en Docker y una máquina de control.

    python correr.py levantar                  # crea la red cd800 y los 51 contenedores cd800-*
    python correr.py <escenario> [...]         # ejecuta escenarios con el laboratorio ya levantado
    python correr.py bajar                     # borra los cd800-* y la red

Escenarios funcionales (sin cronómetro, se pueden correr siempre): uno codigos ingenuo known ansible igual lineas
Escenarios cronometrados (SOLO con el candado _logs/banco.lock): tiempos

Solo crea y borra contenedores cd800-* y la red cd800 (10.80.0.0/24). Todos con --rm.
Roles: s13 «lleno» (sale con 2), s46 con la llave de OTRO cliente en authorized_keys (llave mala),
s48 congelado (docker pause: acepta TCP y nunca manda el banner), s49 lento (tarda 30 s), s50 apagado (docker stop).
Cada escenario deja su salida sin editar en salidas/<escenario>.txt; SALIDA.md se escribe copiando de ahí.
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).parent
SAL = AQUI / "salidas"
SAL.mkdir(exist_ok=True)
ENV = {**os.environ, "MSYS_NO_PATHCONV": "1"}
RED = "cd800"
CLI = "cd800-control"
N = 50
HOSTS = [f"s{i:02d}" for i in range(1, N + 1)]
ROL = {"s13": "lleno", "s49": "lento"}
KH = "/root/.ssh/known_hosts"
F = "cd /root && python flota.py"
A = "cd /root && ansible"


def ip(h):
    return f"10.80.0.{10 + int(h[1:])}"


def sh(*a, check=True, tope=None):
    r = subprocess.run(list(a), capture_output=True, text=True, env=ENV, encoding="utf-8", errors="replace", timeout=tope)
    if check and r.returncode != 0:
        raise SystemExit(f"falló {' '.join(a)}:\n{r.stdout}{r.stderr}")
    return r.stdout.strip()


def ex(cmd, tope=300):
    """Ejecuta en la máquina de control y devuelve «$ cmd» + la salida (stdout y stderr juntos)."""
    r = subprocess.run(["docker", "exec", "-w", "/root", CLI, "bash", "-c", "{ " + cmd + "\n} 2>&1"], capture_output=True,
                       text=True, env=ENV, encoding="utf-8", errors="replace", timeout=tope)
    return f"$ {cmd}\n{r.stdout.rstrip()}\n"


def guardar(nombre, texto):
    (SAL / f"{nombre}.txt").write_text(texto, encoding="utf-8", newline="\n")
    print(f"--- {nombre}\n{texto}")


def bajar():
    nombres = sh("docker", "ps", "-aq", "--filter", "name=^cd800-").split()
    if nombres:
        sh("docker", "unpause", *nombres, check=False)
        sh("docker", "rm", "-f", *nombres, check=False)
    sh("docker", "network", "rm", RED, check=False)


def esperar_ssh(h):
    for _ in range(60):
        if "ssh-ed25519" in sh("docker", "exec", CLI, "ssh-keyscan", "-T", "2", "-t", "ed25519", h, check=False):
            return
        time.sleep(0.5)
    raise SystemExit(f"{h} no levantó sshd")


def levantar():
    bajar()
    sh("docker", "network", "create", "--subnet", "10.80.0.0/24", RED)
    hosts = [a for h in HOSTS for a in ("--add-host", f"{h}:{ip(h)}")]
    sh("docker", "run", "-d", "--rm", "--name", CLI, "--cpus", "1", "--memory", "1g", "--network", RED, "--ip", "10.80.0.5",
       *hosts, "cd800-control:1")
    sh("docker", "exec", CLI, "ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "flota-800", "-f", "/root/.ssh/id_ed25519")
    sh("docker", "exec", CLI, "ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "otro-cliente", "-f", "/root/otra_llave")
    pub = sh("docker", "exec", CLI, "cat", "/root/.ssh/id_ed25519.pub")
    otra = sh("docker", "exec", CLI, "cat", "/root/otra_llave.pub")
    for h in HOSTS:
        sh("docker", "run", "-d", "--rm", "--name", f"cd800-{h}", "--hostname", h, "--network", RED, "--ip", ip(h),
           "--cpus", "0.25", "--memory", "48m", "-e", f"CLAVE_PUB={otra if h == 's46' else pub}",
           "-e", f"ROL={ROL.get(h, 'normal')}", "cd800-sshd:1")
    for h in HOSTS:
        esperar_ssh(h)
    # known_hosts: la huella de cada servidor, tomada con todos sanos (en la vida real: al darlos de alta).
    sh("docker", "exec", CLI, "bash", "-c", f"ssh-keyscan -T 3 {' '.join(HOSTS)} > {KH} 2>/dev/null")
    sh("docker", "exec", CLI, "bash", "-c", "touch /root/known_hosts_vacio")
    tmp = Path(tempfile.mkdtemp(prefix="cd800-"))
    listas = {"hosts-50.txt": HOSTS, "s01.txt": ["s01"], "s13.txt": ["s13"], "s46.txt": ["s46"], "s48.txt": ["s48"],
              "s49.txt": ["s49"], "s50.txt": ["s50"],
              "hosts-sanos.txt": [h for h in HOSTS if h not in ("s46", "s48", "s49", "s50")]}
    for nombre, hs in listas.items():
        (tmp / nombre).write_text("\n".join(hs) + "\n", encoding="utf-8", newline="\n")
        sh("docker", "cp", str(tmp / nombre), f"{CLI}:/root/{nombre}")
    ini = "[flota]\n" + "\n".join(HOSTS) + "\n"
    (tmp / "inventario.ini").write_text(ini, encoding="utf-8", newline="\n")
    sh("docker", "cp", str(tmp / "inventario.ini"), f"{CLI}:/root/inventario.ini")
    for f in ("flota.py", "revisar.yml", "ansible.cfg", "comparar.py"):
        sh("docker", "cp", str(AQUI / f), f"{CLI}:/root/{f}")
    # Los que fallan sin ser culpa del comando: s48 congelado (acepta TCP y no contesta), s50 apagado (nadie en su IP).
    sh("docker", "pause", "cd800-s48")
    sh("docker", "stop", "-t", "1", "cd800-s50")
    print("laboratorio arriba:", sh("docker", "ps", "-q", "--filter", "name=^cd800-").count("\n") + 1, "contenedores")


def e_versiones():
    t = ex("python --version; python -c 'import asyncssh; print(\"asyncssh\", asyncssh.__version__)'; ansible --version | head -1; ssh -V")
    t += ex(f"grep -vc '^#' {KH}; wc -l < hosts-50.txt")
    guardar("versiones", t)


def e_uno():
    t = ex(f"{F} -hosts s01.txt; echo \"código de salida: $?\"")
    t += ex(f"{F} -hosts s13.txt; echo \"código de salida: $?\"")
    guardar("uno", t)


def e_codigos():
    guardar("codigos", ex(f"{F} -hosts hosts-50.txt -p 50; echo \"código de salida: $?\""))


def e_orden():
    t = ex(f"{F} -hosts hosts-sanos.txt -p 50 -llegada > llegada.txt; head -6 llegada.txt")
    t += ex(f"{F} -hosts hosts-sanos.txt -p 50 | head -6")
    guardar("orden", t)


def e_ingenuo():
    t = ex(f"time timeout 200 {F[11:]} -ingenuo -hosts s48.txt; echo \"código de salida: $?\"", tope=260)
    t += ex(f"{F} -ingenuo -hosts s49.txt", tope=120)
    t += ex(f"{F} -ingenuo -hosts s50.txt", tope=260)
    guardar("ingenuo", t)


def e_known():
    t = ex(f"{F} -hosts s01.txt -known known_hosts_vacio; echo \"código de salida: $?\"")
    guardar("known", t)


def e_ansible():
    t = ex(f"{A} all -m raw -a revisar -f 50 -T 3 > adhoc.txt 2>&1; echo \"código de salida: $?\"; "
           "grep -E '^s(01|13|46|48|49|50) ' adhoc.txt", tope=200)
    t += ex(f"{A}-playbook revisar.yml -f 50 -T 3 > play.txt 2>&1; echo \"código de salida: $?\"; "
            "grep -E '^fatal' play.txt; grep -E '^s(01|13|46|48|49|50) ' play.txt", tope=200)
    guardar("ansible", t)


def e_igual():
    guardar("igual", ex("python comparar.py; echo \"código de salida: $?\"", tope=300))


def e_lineas():
    guardar("lineas", ex("grep -cv '^\\s*$' flota.py; grep -cv '^\\s*$' revisar.yml"))


def e_tiempos_ansible():
    """CRONOMETRADO: solo con el candado. Repite la parte de Ansible (la 1.ª corrida cronometró el «cd», no ansible)."""
    t = ""
    for f in (5, 10, 50):
        for _ in range(2):
            t += ex(f"time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f {f} > /dev/null", tope=200)
    for _ in range(2):
        t += ex("time ansible-playbook revisar.yml -f 50 -T 3 > /dev/null", tope=200)
    guardar("tiempos_ansible", t)


def e_tiempos():
    """CRONOMETRADO: solo con el candado _logs/banco.lock tomado."""
    t = ""
    for p in (1, 10, 50):
        for _ in range(2):
            t += ex(f"{F} -hosts hosts-sanos.txt -p {p} | tail -1", tope=200)
    for f in (5, 10, 50):
        for _ in range(2):
            t += ex(f"time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f {f} > /dev/null", tope=200)
    for _ in range(2):
        t += ex(f"{F} -hosts hosts-50.txt -p 50 | tail -1", tope=200)
        t += ex(f"time ansible-playbook revisar.yml -f 50 -T 3 > /dev/null", tope=200)
    guardar("tiempos", t)


if __name__ == "__main__":
    for e in sys.argv[1:]:
        {"levantar": levantar, "bajar": bajar}.get(e, globals().get(f"e_{e}"))()
