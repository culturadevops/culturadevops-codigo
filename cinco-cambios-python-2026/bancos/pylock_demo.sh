#!/bin/sh
# 715 · PEP 751: uv escribe pylock.toml y pip 26.2.2 lo instala. Todo dentro de /tmp del contenedor (v715-banco:1).
set -u
cd "$(mktemp -d)"
echo '$ uv --version'; uv --version
echo '$ python -m pip --version'; python -m pip --version | cut -d' ' -f1-2
uv init --bare -q --python python
echo '$ uv add requests==2.34.2 pyyaml==6.0.3'; uv add -q requests==2.34.2 pyyaml==6.0.3
echo '$ uv export --format pylock.toml -o pylock.toml'; uv export -q --format pylock.toml -o pylock.toml
echo '$ head -12 pylock.toml'; grep -v '^#' pylock.toml | head -12
echo "paquetes en el lock: $(grep -c '^\[\[packages\]\]' pylock.toml) · hashes sha256: $(grep -o 'sha256 = ' pylock.toml | wc -l)"
python -m venv --without-pip /tmp/v1
echo '$ pip install -r pylock.toml'
python -m pip --python /tmp/v1/bin/python install -q --disable-pip-version-check -r pylock.toml; echo "# exit=$?"
echo '$ pip freeze'; python -m pip --python /tmp/v1/bin/python freeze
# Un byte cambiado en el hash del wheel de requests: pip tiene que negarse.
python - <<'PY'
import re, pathlib
p = pathlib.Path("pylock.toml"); s = p.read_text()
i = s.index('name = "requests"'); j = s.index("sha256 = \"", s.index("wheels = [", i)) + len("sha256 = \"")
p.write_text(s[:j] + ("0" if s[j] != "0" else "1") + s[j + 1:])
PY
python -m venv --without-pip /tmp/v2
echo '$ pip install -r pylock.toml   # con un carácter cambiado en el hash de requests'
python -m pip --python /tmp/v2/bin/python install -q --no-cache-dir --disable-pip-version-check -r pylock.toml > /tmp/err.txt 2>&1; rc=$?
grep -v '^ *$' /tmp/err.txt | head -6; echo "# exit=$rc"
echo '$ pip lock requests==2.34.2 -o pylock.pip.toml   # pip también lo escribe (experimental)'
python -m pip lock -q --disable-pip-version-check requests==2.34.2 -o pylock.pip.toml 2>&1 | tail -2
grep -E '^(lock-version|created-by)' pylock.pip.toml
