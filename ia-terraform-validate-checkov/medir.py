# -*- coding: utf-8 -*-
"""Mide un lote/ronda: terraform init -backend=false + validate, Checkov y trivy config. Todo en Docker, sin AWS.

  python medir.py qwen-s1 r0
Escribe medidas/<lote>-<ronda>.json.
"""
import json
import pathlib
import re
import subprocess
import sys

from peticiones import SUPRESIONES, categoria

AQUI = pathlib.Path(__file__).parent
TF = "hashicorp/terraform:1.16.7"
CHECKOV = "bridgecrew/checkov:3.3.30"
TRIVY = "aquasec/trivy:0.76.1"

SH_TF = r"""
for d in /src/*/; do
  n=$(basename "$d"); mkdir -p /work/$n /out/$n; cp "$d"main.tf /work/$n/
  terraform -chdir=/work/$n init -backend=false -input=false -no-color > /out/$n/init.log 2>&1; echo $? > /out/$n/init.rc
  terraform -chdir=/work/$n validate -json -no-color > /out/$n/validate.json 2>/out/$n/validate.err; echo $? > /out/$n/validate.rc
  cp /work/$n/.terraform.lock.hcl /out/$n/ 2>/dev/null || true
done
"""


def docker(args, **kw):
    return subprocess.run(["docker", "run", "--rm"] + args, capture_output=True, text=True, encoding="utf-8", **kw)


def main():
    lote, ronda = sys.argv[1], sys.argv[2]
    src = AQUI / "generado" / lote / ronda
    out = AQUI / "medidas" / "_tf" / f"{lote}-{ronda}"
    out.mkdir(parents=True, exist_ok=True)
    env = ["-e", "AWS_ACCESS_KEY_ID=", "-e", "AWS_SECRET_ACCESS_KEY=", "-e", "TF_PLUGIN_CACHE_DIR=/cache",
           "-e", "TF_IN_AUTOMATION=1", "-e", "CHECKPOINT_DISABLE=1"]
    docker(["--name", f"v706-tf-{lote}-{ronda}", "--cpus", "2", "-v", f"{src}:/src:ro", "-v", f"{out}:/out",
            "-v", "v706-tfcache:/cache"] + env + ["--entrypoint", "sh", TF, "-c", SH_TF])
    ck = docker(["--name", f"v706-ck-{lote}-{ronda}", "--cpus", "2", "-v", f"{src}:/src:ro", CHECKOV,
                 "-d", "/src", "--framework", "terraform", "-o", "json", "--skip-download"])
    tv = docker(["--name", f"v706-tv-{lote}-{ronda}", "--cpus", "2", "-v", f"{src}:/src:ro", "-v", "v706-trivycache:/root/.cache",
                 TRIVY, "config", "-f", "json", "--quiet", "/src"])
    ckj = json.loads(ck.stdout) if ck.stdout.strip().startswith(("{", "[")) else []
    ckj = ckj if isinstance(ckj, list) else [ckj]
    tvj = json.loads(tv.stdout) if tv.stdout.strip().startswith("{") else {}

    mods = {}
    for d in sorted(p for p in src.iterdir() if p.is_dir()):
        n = d.name
        if not (out / n / "init.rc").exists():
            continue
        code = (d / "main.tf").read_text(encoding="utf-8")
        o = out / n
        vj = {}
        try:
            vj = json.loads((o / "validate.json").read_text(encoding="utf-8") or "{}")
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        lock = (o / ".terraform.lock.hcl").read_text(encoding="utf-8") if (o / ".terraform.lock.hcl").exists() else ""
        mods[n] = {
            "vacio": not code.strip(),
            "init_ok": (o / "init.rc").read_text().strip() == "0",
            "validate_ok": bool(vj.get("valid")) and (o / "init.rc").read_text().strip() == "0",
            "validate_errores": [x.get("summary") for x in vj.get("diagnostics", []) if x.get("severity") == "error"][:5],
            "init_error": "" if (o / "init.rc").read_text().strip() == "0" else
            " ".join(l for l in (o / "init.log").read_text(encoding="utf-8").splitlines() if "Error" in l)[:300],
            "aws_provider": (re.findall(r'provider "registry.terraform.io/hashicorp/aws" \{\s*version\s*=\s*"([^"]+)"', lock) or ["-"])[0],
            "ck_fail": [], "ck_pass": 0, "ck_skip": 0, "tv_fail": [],
            "supresiones": sum(len(re.findall(s, code, re.I)) for s in SUPRESIONES),
            "abre_0000": bool(re.search(r"0\.0\.0\.0/0", code)),
        }
    for r in ckj:
        res = r.get("results", {})
        for c in res.get("failed_checks", []):
            n = c["file_path"].strip("/").split("/")[0]
            if n in mods:
                mods[n]["ck_fail"].append([c["check_id"], c["check_name"], c["resource"], categoria(c["check_name"])])
        for c in res.get("passed_checks", []):
            n = c["file_path"].strip("/").split("/")[0]
            if n in mods:
                mods[n]["ck_pass"] += 1
        for c in res.get("skipped_checks", []):
            n = c["file_path"].strip("/").split("/")[0]
            if n in mods:
                mods[n]["ck_skip"] += 1
    for r in tvj.get("Results", []) or []:
        n = r["Target"].strip("/").split("/")[0]
        for m in r.get("Misconfigurations", []) or []:
            if n in mods and m.get("Status") == "FAIL":
                mods[n]["tv_fail"].append([m["ID"], m["Severity"], m["Title"]])
    versiones = {"checkov": docker([CHECKOV, "--version"]).stdout.strip(),
                 "trivy": docker([TRIVY, "--version"]).stdout.strip().splitlines()[0],
                 "terraform": docker([TF, "version"]).stdout.strip().splitlines()[0]}
    dest = AQUI / "medidas" / f"{lote}-{ronda}.json"
    dest.write_text(json.dumps({"lote": lote, "ronda": ronda, "versiones": versiones, "modulos": mods,
                                "ck_stderr": ck.stderr[-500:], "tv_stderr": tv.stderr[-500:]}, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    ok = sum(m["validate_ok"] for m in mods.values())
    limpio = sum(m["validate_ok"] and not m["ck_fail"] for m in mods.values())
    print(f"{lote} {ronda}: {len(mods)} módulos · validate OK {ok} · Checkov sin fallas {limpio} · "
          f"fallas Checkov {sum(len(m['ck_fail']) for m in mods.values())} · trivy {sum(len(m['tv_fail']) for m in mods.values())}")


if __name__ == "__main__":
    main()
