# -*- coding: utf-8 -*-
"""Saca los nombres de paquete de las respuestas y los comprueba contra la API pública de PyPI. NO instala nada.

  python analizar.py            → medidas/analisis.json
Solo hace GET a https://pypi.org/pypi/<nombre>/json (200 = existe, 404 = no existe). Cachea en medidas/pypi_cache.json.
"""
import ast
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

from peticiones import IMPORT_A_PAQUETE

AQUI = pathlib.Path(__file__).parent
CACHE_F = AQUI / "medidas" / "pypi_cache.json"
STDLIB = set(sys.stdlib_module_names) | {"__future__"}
FLAGS_CON_VALOR = {"-r", "--requirement", "-c", "--constraint", "-i", "--index-url", "--extra-index-url", "-f", "--find-links",
                   "-t", "--target", "-e", "--editable"}


def norm(n):
    return re.sub(r"[-_.]+", "-", n).lower()


def cargar_cache():
    return json.loads(CACHE_F.read_text(encoding="utf-8")) if CACHE_F.exists() else {}


def pypi(nombre, cache):
    k = norm(nombre)
    if k in cache:
        return cache[k]
    url = f"https://pypi.org/pypi/{k}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "cultura-devops-v707-medicion (solo lectura)"})
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            rel = d.get("releases", {})
            fechas = sorted(f["upload_time"] for v in rel.values() for f in v if f.get("upload_time"))
            cache[k] = {"existe": True, "nombre": d["info"]["name"], "versiones": len(rel),
                        "primera": fechas[0][:10] if fechas else None, "ultima": fechas[-1][:10] if fechas else None,
                        "resumen": (d["info"].get("summary") or "")[:120]}
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[k] = {"existe": False}
                break
            time.sleep(2 * (intento + 1))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2 * (intento + 1))
    else:
        cache[k] = {"existe": None}
    cache[k]["consultado"] = time.strftime("%Y-%m-%d")
    CACHE_F.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    time.sleep(0.1)
    return cache[k]


def pip_nombres(texto):
    noms = []
    for m in re.finditer(r"pip3?\s+install\s+([^\n`]+)", texto):
        toks = m.group(1).replace("\\", " ").split()
        saltar = False
        for t in toks:
            if saltar:
                saltar = False
                continue
            if t in FLAGS_CON_VALOR:
                saltar = True
                continue
            if t.startswith("-") or t in ("&&", "|", ";", "#") or t.startswith("#"):
                if t.startswith("#") or t in ("&&", "|", ";"):
                    break
                continue
            t = t.strip("'\"`,;:")
            t = re.split(r"[\[<>=!~;@ ]", t)[0]
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", t) and not t.endswith((".txt", ".py", ".whl")) and t.lower() not in ("pip", "install"):
                noms.append(t)
    return noms


def codigo(texto):
    return "\n".join(m.group(1) for m in re.finditer(r"```(?:python|py|python3)?[^\n]*\n(.*?)```", texto, re.S | re.I))


def imports(code):
    mods = set()
    try:
        arbol = ast.parse(code)
        for n in ast.walk(arbol):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                mods.add(n.module.split(".")[0])
    except SyntaxError:
        for m in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", code, re.M):
            mods.add(m.group(1))
    return sorted(m for m in mods if m not in STDLIB)


def analizar_lote(d, cache):
    filas = []
    for f in sorted(d.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        t = r["texto"]
        pips = list(dict.fromkeys(pip_nombres(t)))
        imps = imports(codigo(t))
        fila = {"id": f.stem, "pip": [], "imports": []}
        for p in pips:
            fila["pip"].append([p, pypi(p, cache)["existe"]])
        for i in imps:
            if i.endswith(("_pb2", "_pb2_grpc")) or i.startswith("your_"):
                fila.setdefault("locales", []).append(i)  # stubs generados o módulos propios del ejemplo
                continue
            paq = IMPORT_A_PAQUETE.get(i, i)
            mismo = paq is None or norm(paq) == norm(i)
            if paq is None:
                continue
            e = pypi(paq, cache)["existe"]
            en_pip = any(norm(p) == norm(paq) for p in pips)
            lit = pypi(i, cache) if not mismo else None
            fila["imports"].append({"import": i, "paquete": paq, "distinto": not mismo, "existe": e, "en_pip": en_pip,
                                    "literal_existe": lit["existe"] if lit else None})
        filas.append(fila)
    return filas


def main():
    cache = cargar_cache()
    res = {}
    for d in sorted((AQUI / "respuestas").iterdir()):
        if d.is_dir():
            res[d.name] = analizar_lote(d, cache)
            print(d.name, len(res[d.name]), "respuestas", flush=True)
    (AQUI / "medidas" / "analisis.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
