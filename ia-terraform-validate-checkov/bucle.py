# -*- coding: utf-8 -*-
"""El bucle IA + verificador: rondas 1..3. En cada ronda, a cada módulo con fallas se le devuelven las fallas de Checkov
(y los errores de validate, si los hay) y se pide el main.tf corregido. Los módulos sin fallas pasan tal cual.

  python bucle.py qwen-s1 3
  python bucle.py claude 3 --solo s3-backups sg-web rds-postgres eks ec2-ubuntu   (muestra fijada de antemano)
Tras cada ronda llama a medir.py. Cuenta las supresiones nuevas (#checkov:skip, #trivy:ignore) en medir.py.
"""
import json
import pathlib
import shutil
import subprocess
import sys

from llm import bloques, claude, qwen
from peticiones import ARREGLO

AQUI = pathlib.Path(__file__).parent


def main():
    args = sys.argv[1:]
    lote, rondas = args[0], int(args[1])
    solo = set(args[args.index("--solo") + 1:]) if "--solo" in args else None
    seed = int(lote.split("-s")[1]) if lote.startswith("qwen") else 0
    for k in range(1, rondas + 1):
        prev = AQUI / "generado" / lote / f"r{k - 1}"
        cur = AQUI / "generado" / lote / f"r{k}"
        med = json.loads((AQUI / "medidas" / f"{lote}-r{k - 1}.json").read_text(encoding="utf-8"))["modulos"]
        for slug, m in med.items():
            if solo and slug not in solo:
                continue
            d = cur / slug
            if (d / "main.tf").exists():
                continue
            d.mkdir(parents=True, exist_ok=True)
            fallas = [f"- {c[0]} {c[1]} ({c[2]})" for c in m["ck_fail"]]
            fallas += [f"- terraform validate: {e}" for e in m["validate_errores"]]
            if not m["init_ok"]:
                fallas.append(f"- terraform init: {m['init_error'][:200]}")
            if not fallas:
                shutil.copy(prev / slug / "main.tf", d / "main.tf")
                continue
            codigo = (prev / slug / "main.tf").read_text(encoding="utf-8")
            prompt = ARREGLO.format(codigo=codigo, fallas="\n".join(fallas))
            r = qwen(prompt, seed) if lote.startswith("qwen") else claude(prompt)
            nuevo = bloques(r["texto"]) or codigo
            (d / "main.tf").write_text(nuevo, encoding="utf-8")
            r["prompt"] = prompt
            (d / "respuesta.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
            print(lote, f"r{k}", slug, len(fallas), "fallas →", r.get("s"), "s", flush=True)
        subprocess.run([sys.executable, str(AQUI / "medir.py"), lote, f"r{k}"], check=True)


if __name__ == "__main__":
    main()
