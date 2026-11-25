# -*- coding: utf-8 -*-
"""La «revisión mínima» que sale en pantalla, ejecutada de verdad sobre la app n2 con el Dockerfile de Claude Code (ronda 1).
Añade la salida a SALIDA.md y borra todo lo que crea (v711-mi-app, v711-prueba)."""
import os
import subprocess
import time

import banco

AQUI = banco.AQUI
DF = os.path.join(AQUI, "muestras", "claude", "n2-http-sin-dependencias", "r1.Dockerfile")
CTX = os.path.join(AQUI, "apps", "n2-http-sin-dependencias")


def paso(L, mostrar, args, **kw):
    r = banco.docker(args, **kw) if args[0] != "curl" else subprocess.run(args, capture_output=True, text=True)
    L.append(f"$ {mostrar}")
    salida = (r.stdout + r.stderr).strip().splitlines()
    L.extend(salida[-3:])
    return r


def main():
    L = ["\n## Revisión mínima (revision_minima.py, app n2, Dockerfile de Claude Code ronda 1)\n", "```"]
    with open(DF, encoding="utf-8") as f:
        txt = f.read()
    paso(L, "hadolint Dockerfile", ["run", "--rm", "-i", banco.HADOLINT, "hadolint", "-"], input=txt)
    L.append("(sin salida = 0 avisos)")
    paso(L, "docker build -t v711-mi-app .", ["build", "-q", "-t", "v711-mi-app", "-f", DF, CTX], timeout=900)
    paso(L, "docker run --rm -d -p 18711:8080 --name v711-prueba v711-mi-app",
         ["run", "--rm", "-d", "-p", "18711:8080", "--name", "v711-prueba", "v711-mi-app"])
    time.sleep(3)
    paso(L, "curl -s localhost:18711/", ["curl", "-s", "localhost:18711/"])
    paso(L, "docker image inspect -f '{{.Config.User}}' v711-mi-app", ["image", "inspect", "-f", "{{.Config.User}}", "v711-mi-app"])
    paso(L, "docker images v711-mi-app", ["images", "v711-mi-app"])
    banco.docker(["rm", "-f", "v711-prueba"])
    banco.docker(["rmi", "-f", "v711-mi-app"])
    L.append("```")
    with open(os.path.join(AQUI, "SALIDA.md"), "a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
