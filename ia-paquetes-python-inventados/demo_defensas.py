# -*- coding: utf-8 -*-
"""Demos de terminal del 707: pip-audit NO detecta un paquete inventado; lo que sí lo frena.

⛔ Nunca se instala un paquete inventado. Antes de cada comando de pip se comprueba que el nombre inventado da 404 en PyPI;
si alguien lo hubiera registrado, el script para sin ejecutar nada. Todo corre en Docker con --rm (python:3.12.16-bookworm).
Escribe medidas/demo_defensas.txt con la salida literal.
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

AQUI = pathlib.Path(__file__).parent
INVENTADO = "dockerfile-py"   # lo pidió qwen2.5:7b en n03 («leer y modificar un Dockerfile»); el real es dockerfile-parse
IMG = "python:3.12.16-bookworm"


def existe(n):
    try:
        urllib.request.urlopen(f"https://pypi.org/pypi/{n}/json", timeout=30)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def hash_wheel(n, v):
    with urllib.request.urlopen(f"https://pypi.org/pypi/{n}/{v}/json", timeout=30) as r:
        d = json.load(r)
    return [u["digests"]["sha256"] for u in d["urls"] if u["packagetype"] == "bdist_wheel"][0]


def main():
    if existe(INVENTADO):
        sys.exit(f"⛔ {INVENTADO} ya existe en PyPI: no se ejecuta nada.")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="v707-"))
    (tmp / "requirements.txt").write_text(f"requests==2.34.2\n{INVENTADO}==1.0.0\n", encoding="utf-8")
    (tmp / "requirements.lock").write_text(f"requests==2.34.2 --hash=sha256:{hash_wheel('requests', '2.34.2')}\n"
                                           "six==1.17.0\n", encoding="utf-8")
    # n33: qwen escribió `import journal` para leer el journal de systemd. En PyPI, «journal» es otra cosa (un CLI de 2015).
    (tmp / "requirements-journal.txt").write_text("journal==0.4.0\n", encoding="utf-8")
    import shutil
    shutil.copy(AQUI / "verificar_paquetes.py", tmp / "verificar_paquetes.py")
    sh = f"""
set +e
pip install -q --root-user-action=ignore --disable-pip-version-check pip-audit==2.10.1 >/dev/null 2>&1
for n in dockerfile-py dockerfile-parse hcl2 python-hcl2 yaml pyyaml; do
  echo "\$ curl -s -o /dev/null -w '%{{http_code}}\\n' https://pypi.org/pypi/$n/json"
  curl -s -o /dev/null -w '%{{http_code}}\\n' https://pypi.org/pypi/$n/json
done
echo '$ cat requirements.txt'; cat requirements.txt
echo '$ pip-audit --version'; pip-audit --version
echo '$ pip-audit -r requirements.txt --no-deps --disable-pip'
pip-audit -r requirements.txt --no-deps --disable-pip --progress-spinner off 2>&1 | grep -v -E 'WARNING|pip-compile'; echo "# exit=$?"
echo '$ pip-audit -r requirements.txt --no-deps --disable-pip --strict'
pip-audit -r requirements.txt --no-deps --disable-pip --strict --progress-spinner off 2>&1 | grep -v -E 'WARNING|pip-compile'; echo "# exit=${{PIPESTATUS[0]}}"
echo '$ python verificar_paquetes.py requirements.txt'
python verificar_paquetes.py requirements.txt; echo "# exit=$?"
echo '$ cat requirements-journal.txt'; cat requirements-journal.txt
echo '$ pip-audit -r requirements-journal.txt --no-deps --disable-pip --strict'
pip-audit -r requirements-journal.txt --no-deps --disable-pip --strict --progress-spinner off 2>&1 | grep -v -E 'WARNING|pip-compile'; echo "# exit=${{PIPESTATUS[0]}}"
echo '$ python verificar_paquetes.py requirements-journal.txt'
python verificar_paquetes.py requirements-journal.txt; echo "# exit=$?"
echo '$ cat requirements.lock'; sed -E 's/(sha256:.{{12}}).*/\\1…/' requirements.lock
echo '$ pip install --require-hashes --no-deps --dry-run -r requirements.lock'
pip install --require-hashes --no-deps --dry-run --disable-pip-version-check -r requirements.lock 2>&1 | grep -v -E '^\\[notice\\]'; echo "# exit=${{PIPESTATUS[0]}}"
"""
    p = subprocess.run(["docker", "run", "--rm", "--name", "v707-defensas", "--cpus", "2", "-v", f"{tmp}:/d", "-w", "/d", IMG,
                        "bash", "-c", sh], capture_output=True, text=True, encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    salida = p.stdout + p.stderr
    (AQUI / "medidas" / "demo_defensas.txt").write_text(salida, encoding="utf-8")
    print(salida)


if __name__ == "__main__":
    main()
