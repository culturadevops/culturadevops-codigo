"""dockerfile_ia.py — un LLM local (Ollama) escribe el Dockerfile de un proyecto y lo arregla con los errores de docker build.

    python dockerfile_ia.py <carpeta-del-proyecto> [--modelo qwen2.5-coder:7b] [--intentos 4] [--errores cola|relevantes]

Solo biblioteca estándar. Pasos: 1) lee los archivos del proyecto; 2) pide el Dockerfile; 3) docker build; si falla, le devuelve
el error al modelo y vuelve a pedir; 4) si construye, arranca el contenedor y comprueba GET /salud. Imprime cada intento.
"""
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

OLLAMA = "http://127.0.0.1:11434/api/chat"
PUERTO = 8080


def leer_proyecto(carpeta):
    partes = []
    for f in sorted(carpeta.rglob("*")):
        if f.is_file() and f.stat().st_size < 4000 and f.name != "Dockerfile":
            partes.append(f"--- {f.relative_to(carpeta).as_posix()} ---\n{f.read_text(encoding='utf-8')}")
    return "\n".join(partes)


def preguntar(modelo, mensajes):
    cuerpo = json.dumps({"model": modelo, "messages": mensajes, "stream": False,
                         "options": {"temperature": 0, "seed": 42}}).encode()
    req = urllib.request.Request(OLLAMA, data=cuerpo, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"]


def extraer_dockerfile(texto):
    m = re.search(r"```(?:dockerfile|Dockerfile)?\s*\n(.*?)```", texto, re.S)
    return (m.group(1) if m else texto).strip() + "\n"


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


RELEVANTE = re.compile(r"(?i)error|not found|no such|cannot|missing|failed|requires")


def resumen_error(log, modo):
    lineas = [l for l in log.strip().splitlines() if "preface" not in l]
    if modo == "cola":                                   # v1: solo las últimas 15 líneas
        return "\n".join(lineas[-15:])
    vistas, salida = set(), []                           # v2: las líneas que dicen POR QUÉ, de todo el log
    for l in [l for l in lineas if RELEVANTE.search(l)] + lineas[-5:]:
        clave = re.sub(r"^#\d+ [\d.]+ ", "", l)
        if clave not in vistas:
            vistas.add(clave)
            salida.append(clave)
    return "\n".join(salida[-25:])


def probar(carpeta, etiqueta, modo):
    b = sh(["docker", "build", "--progress=plain", "-t", etiqueta, "."], cwd=carpeta)
    if b.returncode != 0:
        return False, "docker build falló:\n" + resumen_error(b.stdout + b.stderr, modo)
    sh(["docker", "rm", "-f", "ia-demo"])
    r = sh(["docker", "run", "-d", "--name", "ia-demo", "-p", f"18080:{PUERTO}", etiqueta])
    if r.returncode != 0:
        return False, "docker run falló:\n" + r.stderr.strip()[-800:]
    for _ in range(20):
        time.sleep(1)
        try:
            with urllib.request.urlopen("http://127.0.0.1:18080/salud", timeout=2) as resp:
                cuerpo = resp.read().decode().strip()
                sh(["docker", "rm", "-f", "ia-demo"])
                return True, f"GET /salud -> {resp.status} {cuerpo}"
        except Exception:
            pass
    logs = sh(["docker", "logs", "ia-demo"])
    sh(["docker", "rm", "-f", "ia-demo"])
    return False, "el contenedor arrancó pero /salud no respondió. Logs:\n" + (logs.stdout + logs.stderr).strip()[-800:]


def main():
    carpeta = pathlib.Path(sys.argv[1]).resolve()
    modelo = sys.argv[sys.argv.index("--modelo") + 1] if "--modelo" in sys.argv else "qwen2.5-coder:7b"
    intentos = int(sys.argv[sys.argv.index("--intentos") + 1]) if "--intentos" in sys.argv else 4
    modo = sys.argv[sys.argv.index("--errores") + 1] if "--errores" in sys.argv else "relevantes"
    mensajes = [
        {"role": "system", "content": "Eres un ingeniero DevOps. Respondes SOLO con un Dockerfile dentro de un bloque ```dockerfile."},
        {"role": "user", "content": f"Escribe un Dockerfile de producción para este proyecto. La app debe escuchar en el puerto "
                                    f"{PUERTO} y responder en GET /salud.\n\n{leer_proyecto(carpeta)}"},
    ]
    t0 = time.time()
    for n in range(1, intentos + 1):
        t = time.time()
        respuesta = preguntar(modelo, mensajes)
        dockerfile = extraer_dockerfile(respuesta)
        (carpeta / "Dockerfile").write_text(dockerfile, encoding="utf-8")
        ok, detalle = probar(carpeta, f"ia-demo:{n}", modo)
        print(f"== intento {n} ({time.time() - t:.1f} s)")
        print("".join(f"   | {l}\n" for l in dockerfile.splitlines()), end="")
        print("   -> " + detalle.replace("\n", "\n      "))
        if ok:
            tam = sh(["docker", "image", "inspect", "-f", "{{.Size}}", f"ia-demo:{n}"]).stdout.strip()
            print(f"\nRESULTADO: funciona en el intento {n} · {time.time() - t0:.1f} s en total · imagen de "
                  f"{int(tam) / 1e6:.0f} MB · modelo {modelo}")
            return 0
        mensajes += [{"role": "assistant", "content": respuesta},
                     {"role": "user", "content": f"Ese Dockerfile no funciona. Este es el error:\n{detalle}\n"
                                                 "Corrígelo. Responde solo con el Dockerfile completo."}]
    print(f"\nRESULTADO: no funcionó en {intentos} intentos · {time.time() - t0:.1f} s · modelo {modelo}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
