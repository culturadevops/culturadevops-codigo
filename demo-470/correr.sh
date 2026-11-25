#!/usr/bin/env bash
# Demo del vídeo 470 «OWASP Top 10 de CI/CD» — se EJECUTA y su salida va a SALIDA.md.
# Un auditor de 60 líneas en Python que revisa workflows de GitHub Actions y marca 5 de los 10 riesgos de OWASP
# que se pueden ver leyendo el YAML. Se pasa sobre un workflow «malo» y su versión corregida.
# Todo en un directorio temporal; los «secretos» son de mentira.
set -u
T=$(mktemp -d)
cd "$T"
mkdir -p malo/.github/workflows bueno/.github/workflows

cat > malo/.github/workflows/ci.yml <<'EOF'
on: pull_request_target
permissions: write-all
jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - uses: tj-actions/changed-files@v45
      - run: make test
      - run: curl -H "Authorization: token ghp_EJEMPLOxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" https://api.github.com/user
      - run: echo "${{ secrets.DEPLOY_KEY }}"
EOF

cat > bueno/.github/workflows/ci.yml <<'EOF'
on: pull_request
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@08eba0b27e820071cde6df949e0beb9ba4906955 # v4.3.0
      - run: make test
EOF

cat > auditar.py <<'EOF'
"""Auditor mínimo de GitHub Actions: 5 riesgos del OWASP Top 10 de CI/CD que se ven leyendo el YAML."""
import pathlib
import re
import sys

REGLAS = [
    ("CICD-SEC-4 Poisoned Pipeline Execution",
     lambda t: "pull_request_target" in t and "github.event.pull_request.head" in t,
     "pull_request_target + checkout del código del PR: el código ajeno corre con tus secretos"),
    ("CICD-SEC-5 Insufficient PBAC",
     lambda t: re.search(r"permissions:\s*write-all", t) or "permissions:" not in t,
     "permisos de escritura para todo (o sin declarar)"),
    ("CICD-SEC-3 Dependency Chain Abuse",
     lambda t: re.search(r"uses: [^.\s][^@\s]*@(?![0-9a-f]{40}\b)", t),
     "action de terceros fijada por etiqueta, no por SHA"),
    ("CICD-SEC-6 Insufficient Credential Hygiene",
     lambda t: re.search(r"gh[pousr]_[A-Za-z0-9]{20,}|echo .*secrets\.", t),
     "token escrito en el YAML o secreto impreso en el log"),
    ("CICD-SEC-7 Insecure System Configuration",
     lambda t: "pull_request" in t and "self-hosted" in t,
     "runner propio ejecutando código de pull requests"),
]

total = 0
for wf in sorted(pathlib.Path(sys.argv[1]).rglob("*.yml")):
    texto = wf.read_text(encoding="utf-8")
    hallazgos = [(r, d) for r, f, d in REGLAS if f(texto)]
    total += len(hallazgos)
    print(f"{wf.as_posix()}: {len(hallazgos)} hallazgo(s)")
    for r, d in hallazgos:
        print(f"  [{r}] {d}")
sys.exit(1 if total else 0)
EOF

echo '$ cat malo/.github/workflows/ci.yml'
cat malo/.github/workflows/ci.yml
echo
echo '$ python auditar.py malo'
python auditar.py malo; echo "(código de salida: $?)"
echo
echo '$ cat bueno/.github/workflows/ci.yml'
cat bueno/.github/workflows/ci.yml
echo
echo '$ python auditar.py bueno'
python auditar.py bueno; echo "(código de salida: $?)"
echo
echo '$ wc -l auditar.py'
wc -l < auditar.py
cd / && rm -rf "$T"
