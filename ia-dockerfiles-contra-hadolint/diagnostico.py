# -*- coding: utf-8 -*-
"""Por qué no arrancan las imágenes que sí construyen: las vuelve a construir, las arranca SIN --rm para leer los logs, y borra todo.
Añade el resultado a SALIDA.md. También comprueba con `docker manifest inspect` las imágenes base que no se encontraron."""
import json
import os
import time

import banco

AQUI = banco.AQUI


def main():
    banco.preparar()
    with open(os.path.join(AQUI, "resultados.json"), encoding="utf-8") as f:
        res = json.load(f)
    L = ["\n## Diagnóstico (diagnostico.py)\n"]
    for quien, por_app in res.items():
        for app, rs in por_app.items():
            for r in {0, len(rs) - 1}:
                m = rs[r]["medida"]
                if not m["construye"] or m.get("arranca"):
                    continue
                tag, nombre = f"v711-diag-{quien}-{app}", "v711-diag"
                banco.construir(app, os.path.join(AQUI, m["dockerfile"]), tag)
                banco.docker(["rm", "-f", nombre])
                banco.docker(["run", "-d", "--name", nombre, "--network", banco.RED, "--cpus", "1", "--memory", "1g", tag])
                time.sleep(8)
                est = banco.docker(["inspect", "-f", "{{.State.Status}} exit={{.State.ExitCode}}", nombre]).stdout.strip()
                lg = banco.docker(["logs", nombre])
                ls = [x for x in (lg.stdout + lg.stderr).strip().splitlines() if x.strip()]
                errs = [x.strip() for x in ls if "Error" in x or "error" in x or "No module" in x or "no such file" in x]
                logs = " / ".join(errs[:2] or ls[-2:])[:400]
                banco.docker(["rm", "-f", nombre])
                banco.borrar_imagen(tag)
                L.append(f"- {quien} {app} r{r}: {est} · {logs}")
    vistas = set()
    for quien, por_app in res.items():
        for app, rs in por_app.items():
            for r in rs:
                m = r.get("medida")
                if m and not m["construye"] and "not found" in m["error_build"]:
                    for b in m["bases"]:
                        if b not in vistas and b.startswith("openjdk"):
                            vistas.add(b)
                            out = banco.docker(["manifest", "inspect", b], timeout=60)
                            L.append(f"- docker manifest inspect {b}: {(out.stdout[:60] or out.stderr.strip())[:120]}")
    with open(os.path.join(AQUI, "SALIDA.md"), "a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
