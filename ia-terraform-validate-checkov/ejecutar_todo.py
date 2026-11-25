# -*- coding: utf-8 -*-
"""706 · Regenera SALIDA.md.

  python ejecutar_todo.py            # vuelve a medir TODO lo generado (rondas 0-3) y reescribe SALIDA.md
  python ejecutar_todo.py --sin-medir  # solo reescribe SALIDA.md con las medidas que hay
  python ejecutar_todo.py --generar  # además genera lo que falte (gasta Ollama y la cuenta de Claude)

Generar: generar.py (ronda 0) y bucle.py (rondas 1-3). Medir: medir.py. Todo en Docker, sin AWS.
"""
import collections
import datetime
import json
import pathlib
import re
import subprocess
import sys

from llm import PARAMS, QWEN, qwen_digest
from peticiones import ARREGLO, CATEGORIAS, PETICIONES, PLANTILLA, SUPRESIONES

AQUI = pathlib.Path(__file__).parent
PY = sys.executable
LOTES = ["qwen-s1", "qwen-s2", "claude"]
MUESTRA_CLAUDE = ["s3-backups", "sg-web", "rds-postgres", "eks", "ec2-ubuntu"]
REGLAS = [("CKV_AWS_24", "SSH abierto a 0.0.0.0/0"), ("CKV_AWS_260", "puerto 80 abierto a 0.0.0.0/0"),
          ("CKV_AWS_382", "salida a 0.0.0.0/0, todos los puertos"), ("CKV_AWS_79", "IMDSv1 activo"),
          ("CKV_AWS_8", "disco de EC2 sin cifrar"), ("CKV_AWS_27", "SQS sin cifrar"), ("CKV2_AWS_6", "S3 sin bloqueo de acceso público"),
          ("CKV_AWS_145", "S3 sin KMS"), ("CKV_AWS_16", "RDS sin cifrar"), ("CKV_AWS_17", "RDS pública"),
          ("CKV_AWS_144", "S3 sin replicación entre regiones"), ("CKV_AWS_18", "S3 sin access logging"),
          ("CKV_AWS_158", "logs de CloudWatch sin KMS"), ("CKV_AWS_338", "logs de CloudWatch < 1 año"),
          ("CKV_AWS_88", "EC2 con IP pública"), ("CKV_AWS_23", "security group sin descripción")]


def run(*a):
    subprocess.run([PY, *[str(x) for x in a]], check=True, cwd=AQUI)


def cargar(lote, ronda):
    f = AQUI / "medidas" / f"{lote}-{ronda}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def rondas(lote):
    return sorted(p.name for p in (AQUI / "generado" / lote).iterdir() if p.is_dir())


def resumen(mods):
    v = [m for m in mods.values() if m["validate_ok"]]
    f = sum(len(m["ck_fail"]) for m in mods.values())
    p = sum(m["ck_pass"] for m in mods.values())
    sev = collections.Counter(t[1] for m in mods.values() for t in m["tv_fail"])
    return {"n": len(mods), "init": sum(m["init_ok"] for m in mods.values()), "validate": len(v),
            "limpios": sum(not m["ck_fail"] for m in v), "fallas": f, "pasadas": p,
            "pct": round(100 * f / (f + p), 1) if f + p else 0, "skip": sum(m["ck_skip"] for m in mods.values()),
            "supr": sum(m["supresiones"] for m in mods.values()), "abre": sum(m["abre_0000"] for m in mods.values()),
            "trivy": sum(sev.values()), "crit": sev["CRITICAL"], "high": sev["HIGH"],
            "tv_limpios": sum(not m["tv_fail"] for m in v)}


def tipos_inventados(lote):
    out = []
    for f in sorted((AQUI / "medidas" / "_tf" / f"{lote}-r0").glob("*/validate.json")):
        for t in re.findall(r'does not support resource type \\"([a-z0-9_]+)\\"(?:\. Did you mean \\"([a-z0-9_]+)\\")?',
                            f.read_text(encoding="utf-8")):
            out.append((f.parent.name, t[0], t[1]))
    return sorted(set(out))


def demo_terminal(lote, slug):
    """Salida en texto, tal cual, de validate y Checkov sobre un módulo (para las escenas de terminal)."""
    src = AQUI / "generado" / lote / "r0" / slug
    sh = ("cp -r /src /w && cd /w && terraform init -backend=false -input=false -no-color >/dev/null 2>&1; "
          "terraform validate -no-color 2>&1; echo \"# exit=$?\"")
    tf = subprocess.run(["docker", "run", "--rm", "--name", f"v706-demo-{lote}-{slug}", "-v", f"{src}:/src:ro",
                         "-v", "v706-tfcache:/cache", "-e", "TF_PLUGIN_CACHE_DIR=/cache", "-e", "CHECKPOINT_DISABLE=1",
                         "--entrypoint", "sh", "hashicorp/terraform:1.16.7", "-c", sh], capture_output=True, text=True, encoding="utf-8")
    ck = subprocess.run(["docker", "run", "--rm", "--name", f"v706-demock-{lote}-{slug}", "-v", f"{src}:/src:ro",
                         "bridgecrew/checkov:3.3.30", "-f", "/src/main.tf", "--framework", "terraform", "--compact", "--quiet", "--skip-download"],
                        capture_output=True, text=True, encoding="utf-8")
    ck_lineas = [l for l in ck.stdout.splitlines() if l.startswith(("Passed", "Check:", "terraform scan")) or "FAILED" in l]
    return tf.stdout.strip(), "\n".join(ck_lineas[:40]) + f"\n# exit={ck.returncode}"


def main():
    if "--generar" in sys.argv:
        run("generar.py", "qwen", 1, 2)
        run("generar.py", "claude")
        run("bucle.py", "qwen-s1", 3)
        run("bucle.py", "claude", 3, "--solo", *MUESTRA_CLAUDE)
    if "--sin-medir" not in sys.argv:
        for lote in LOTES:
            for r in rondas(lote):
                run("medir.py", lote, r)

    L = []
    w = L.append
    m0 = cargar("claude", "r0")
    w("# SALIDA · 706 · Terraform escrito por IA: pasa validate y suspende Checkov")
    w(f"\nGenerado por `ejecutar_todo.py` el {datetime.date.today().isoformat()}. Sin cuenta de AWS: solo "
      "`terraform init -backend=false` + `terraform validate`, Checkov y `trivy config`, todo en Docker con `--rm`.")
    w("\n## Versiones\n")
    w(f"- {m0['versiones']['terraform']} (imagen hashicorp/terraform:1.16.7) · Checkov {m0['versiones']['checkov']} "
      f"(bridgecrew/checkov:3.3.30) · Trivy {m0['versiones']['trivy']} (aquasec/trivy:0.76.1)")
    w(f"- Modelo local: `{QWEN}` digest `{qwen_digest()}` vía Ollama `/api/chat`, opciones {json.dumps(PARAMS)} + `seed` 1 y 2.")
    w("- Claude Code 2.1.312, `claude -p --safe-mode --tools \"\" --output-format json --no-session-persistence --max-budget-usd 1`, "
      "desde un directorio temporal vacío y sin variables de credenciales. Modelo que respondió: "
      f"`{json.loads((AQUI / 'generado/claude/r0/s3-backups/respuesta.json').read_text(encoding='utf-8'))['modelo']}`. "
      "La temperatura de Claude Code no se puede fijar: una sola muestra por petición. `--bare` no se usó porque exige "
      "ANTHROPIC_API_KEY y la cuenta es OAuth; `--safe-mode` desactiva CLAUDE.md, hooks, MCP y skills.")
    prov = collections.Counter(m["aws_provider"] for l in LOTES for m in cargar(l, "r0")["modulos"].values())
    w(f"- Versión del proveedor aws que eligió cada módulo (la escribe la IA en required_providers): {dict(prov)}")
    for l in LOTES:
        w(f"  - {l}: " + str(dict(collections.Counter(m["aws_provider"] for m in cargar(l, "r0")["modulos"].values()))))
    import urllib.request
    with urllib.request.urlopen("https://registry.terraform.io/v1/providers/hashicorp/aws", timeout=30) as r:
        reg = json.load(r)
    w(f"- Última versión del proveedor aws en el Registry hoy: {reg['version']} (publicada {reg['published_at'][:10]}).")
    w("\n## Prompt (igual para las dos IA)\n")
    w("```\n" + PLANTILLA + "\n```\n")
    w("Bucle (rondas 1-3), a cada módulo con fallas:\n\n```\n" + ARREGLO + "\n```")
    w("\n## Criterio (fijado antes de generar, peticiones.py)\n")
    w("- 25 peticiones típicas, ninguna menciona la seguridad: " + ", ".join(s for s, _ in PETICIONES) + ".")
    w("- «Válido» = init y validate con salida 0. «Limpio» = válido y Checkov sin ninguna falla.")
    w("- Se cuentan TODAS las fallas de Checkov (framework terraform) y de trivy config, también las que mucha gente considera "
      "ruido (replicación entre regiones, notificaciones de S3…). Checkov y Trivy también escanean los módulos inválidos.")
    w("- Categorías por palabras del nombre de la regla, la primera que casa: " +
      "; ".join(f"{c}: {', '.join(k)}" for c, k in CATEGORIAS) + "; si no, «otras».")
    w("- Supresión = " + ", ".join(f"`{s}`" for s in SUPRESIONES) + " en el código. Checkov también cuenta las que reconoce (skipped).")
    w("- Muestra pequeña (25 peticiones, 50 módulos de qwen y 25 de Claude): esto no es un estudio.")

    w("\n## Ronda 0: lo que sale a la primera\n")
    w("| IA | módulos | init OK | validate OK | limpios (Checkov 0) | fallas Checkov | pasadas | % fallas | trivy FAIL | CRITICAL | HIGH | trivy limpios (válidos) | con 0.0.0.0/0 | supresiones |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for l in LOTES:
        r = resumen(cargar(l, "r0")["modulos"])
        w(f"| {l} | {r['n']} | {r['init']} | {r['validate']} | {r['limpios']} | {r['fallas']} | {r['pasadas']} | {r['pct']} % | "
          f"{r['trivy']} | {r['crit']} | {r['high']} | {r['tv_limpios']} | {r['abre']} | {r['supr']} |")
    w("\n### Fallas de Checkov por categoría (ronda 0)\n")
    cats = [c for c, _ in CATEGORIAS] + ["otras"]
    w("| categoría | " + " | ".join(LOTES) + " |")
    w("|---|" + "---|" * len(LOTES))
    cnt = {l: collections.Counter(c[3] for m in cargar(l, "r0")["modulos"].values() for c in m["ck_fail"]) for l in LOTES}
    for c in cats:
        w(f"| {c} | " + " | ".join(str(cnt[l][c]) for l in LOTES) + " |")
    w("\n### Reglas concretas (fallas en ronda 0)\n")
    w("| regla | qué es | " + " | ".join(LOTES) + " |")
    w("|---|---|" + "---|" * len(LOTES))
    rc = {l: collections.Counter(c[0] for m in cargar(l, "r0")["modulos"].values() for c in m["ck_fail"]) for l in LOTES}
    for rid, q in REGLAS:
        w(f"| {rid} | {q} | " + " | ".join(str(rc[l][rid]) for l in LOTES) + " |")
    w("\n### Las 10 reglas que más fallan, por IA\n")
    for l in LOTES:
        c = collections.Counter((x[0], x[1]) for m in cargar(l, "r0")["modulos"].values() for x in m["ck_fail"])
        w(f"- **{l}**: " + "; ".join(f"{k[0]} {k[1]} ×{v}" for k, v in c.most_common(10)))
    w("\n### Tipos de recurso que no existen (validate: «does not support resource type»)\n")
    for l in LOTES:
        t = tipos_inventados(l)
        w(f"- {l}: {len(t)} — " + ("; ".join(f"{a}: `{b}`" + (f" (¿{c}?)" if c else "") for a, b, c in t) or "ninguno"))
    w("\n### Errores de validate (resumen de Terraform)\n")
    for l in LOTES:
        c = collections.Counter(e for m in cargar(l, "r0")["modulos"].values() for e in m["validate_errores"])
        w(f"- {l}: " + ("; ".join(f"{k} ×{v}" for k, v in c.most_common()) or "ninguno"))

    w("\n## El bucle IA + Checkov (rondas 0-3)\n")
    w("qwen-s1: los 25 módulos. Claude: muestra fijada antes de mirar = " + ", ".join(MUESTRA_CLAUDE) + ".\n")
    w("| IA | ronda | módulos | validate OK | limpios | fallas Checkov | pasadas | trivy FAIL | `#checkov:skip`/ignore en el código | skipped por Checkov | líneas de código | recursos |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for l in ["qwen-s1", "claude"]:
        for r in rondas(l):
            d = cargar(l, r)
            if not d:
                continue
            mods = d["modulos"] if l != "claude" else {k: v for k, v in d["modulos"].items() if k in MUESTRA_CLAUDE}
            s = resumen(mods)
            cods = [(AQUI / "generado" / l / r / k / "main.tf").read_text(encoding="utf-8") for k in mods]
            lin = sum(len(c.splitlines()) for c in cods)
            rec = sum(len(re.findall(r'^resource\s+"', c, re.M)) for c in cods)
            w(f"| {l} | {r} | {s['n']} | {s['validate']} | {s['limpios']} | {s['fallas']} | {s['pasadas']} | {s['trivy']} | {s['supr']} | {s['skip']} | {lin} | {rec} |")
    w("\n### Por módulo en el bucle (fallas Checkov r0→r1→r2→r3; v = validate OK; s = supresiones)\n")
    for l in ["qwen-s1", "claude"]:
        rs = [cargar(l, r) for r in rondas(l)]
        for slug in (MUESTRA_CLAUDE if l == "claude" else [s for s, _ in PETICIONES]):
            fila = []
            for d in rs:
                m = d["modulos"].get(slug) if d else None
                if m:
                    fila.append(f"{len(m['ck_fail'])}{'v' if m['validate_ok'] else '✗'}{('s' + str(m['supresiones'])) if m['supresiones'] else ''}")
            w(f"- {l} {slug}: " + " → ".join(fila))
    w("\n### Supresiones que metió la IA (líneas del código)\n")
    for l in ["qwen-s1", "claude"]:
        for r in rondas(l):
            for f in sorted((AQUI / "generado" / l / r).glob("*/main.tf")):
                for i, lin in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if any(re.search(s, lin, re.I) for s in SUPRESIONES):
                        w(f"- {l} {r} {f.parent.name}:{i}: `{lin.strip()}`")

    w("\n### Claude r0 → r1: qué cambió para que Checkov pase (grep literal)\n")
    pat = r'endpoint_public_access|associate_public_ip_address|from_port\s*=\s*80\b|^resource "aws_network_interface"|^resource "aws_s3_bucket" '
    for slug in MUESTRA_CLAUDE:
        for r in ("r0", "r1"):
            f = AQUI / "generado" / "claude" / r / slug / "main.tf"
            txt = f.read_text(encoding="utf-8")
            hits = [l.strip() for l in txt.splitlines() if re.search(pat, l)]
            w(f"- {slug} {r}: {len(txt.splitlines())} líneas, {len(re.findall(r'^resource ', txt, re.M))} recursos · " +
              ("; ".join(f"`{h}`" for h in hits) or "—"))
    w("\n## Por módulo, ronda 0 (fallas Checkov / trivy; ✗ = no valida)\n")
    w("| petición | " + " | ".join(LOTES) + " |")
    w("|---|" + "---|" * len(LOTES))
    for slug, _ in PETICIONES:
        cel = []
        for l in LOTES:
            m = cargar(l, "r0")["modulos"][slug]
            cel.append(f"{len(m['ck_fail'])} / {len(m['tv_fail'])}{'' if m['validate_ok'] else ' ✗'}")
        w(f"| {slug} | " + " | ".join(cel) + " |")

    w("\n## Demos de terminal (texto literal)\n")
    for l, slug in [("claude", "s3-backups"), ("qwen-s1", "sg-web"), ("qwen-s1", "rds-postgres"), ("claude", "sg-web"), ("qwen-s2", "sqs")]:
        tf, ck = demo_terminal(l, slug)
        w(f"### {l} · {slug}\n\n```\n$ terraform validate\n{tf}\n\n$ checkov -f main.tf --framework terraform --compact --quiet\n{ck}\n```\n")
    (AQUI / "SALIDA.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("SALIDA.md escrito")


if __name__ == "__main__":
    main()
