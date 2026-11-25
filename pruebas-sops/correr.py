# -*- coding: utf-8 -*-
"""SOPS — banco de pruebas del vídeo 330 (cultura-devops, serie herramientas).

Imagen `lab-sops`: la oficial ghcr.io/getsops/sops:v3.13.3-alpine + age, git, yq.
Un contenedor de larga vida con /repo (un repo git) y dos claves age: la mía y la de una compañera.

    python correr.py
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
IMG = "lab-sops"
C = "sops-lab"
salida = []

DOCKERFILE = ("FROM ghcr.io/getsops/sops:v3.13.3-alpine\n"
              "RUN apk add --no-cache age git yq bash\nENTRYPOINT []\n")

SECRETOS = """db:
  host: db.interna
  port: 5432
  user: app
  password: s3cr3t0-de-produccion
api:
  url: https://pagos.ejemplo.test
  token: tok_live_9f8e7d6c5b4a
"""


def sh(cmd, timeout=600, entrada=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, input=entrada)
    return (r.stdout + r.stderr).strip()


def x(script, env=None):
    e = []
    for k, v in (env or {}).items():
        e += ["-e", f"{k}={v}"]
    return sh(["docker", "exec", *e, "-w", "/repo", C, "bash", "-c", script])


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


YO = {"SOPS_AGE_KEY_FILE": "/claves/yo.txt"}
ELLA = {"SOPS_AGE_KEY_FILE": "/claves/ella.txt"}
NADIE = {"SOPS_AGE_KEY_FILE": "/claves/no-existe.txt"}


def main():
    print(sh(["docker", "build", "-q", "-t", IMG, "-"], entrada=DOCKERFILE, timeout=900))
    sh(["docker", "rm", "-f", C])
    sh(["docker", "run", "-d", "--name", C, IMG, "sh", "-c", "mkdir -p /repo /claves && sleep infinity"])
    import time
    time.sleep(2)
    x("git init -q -b main && git config user.email dev@ejemplo.test && git config user.name dev")

    salida.append("\n## 1 · Versiones y claves age")
    anota("versiones", "sops --version; age --version", x("sops --version 2>&1 | head -1; age --version"))
    anota("mi clave", "age-keygen -o /claves/yo.txt", x("age-keygen -o /claves/yo.txt 2>&1"))
    anota("el archivo de la clave", "cat /claves/yo.txt (la privada, recortada)",
          x("sed -E 's/(AGE-SECRET-KEY-1.{6}).*/\\1…(privada)/' /claves/yo.txt"))
    x("age-keygen -o /claves/ella.txt 2>/dev/null")
    pub_yo = x("age-keygen -y /claves/yo.txt")
    pub_ella = x("age-keygen -y /claves/ella.txt")

    salida.append("\n## 2 · .sops.yaml y el primer cifrado")
    sops_yaml = ("creation_rules:\n"
                 "  - path_regex: secretos/.*\\.yaml$\n"
                 "    encrypted_regex: ^(password|token)$\n"
                 f"    age: {pub_yo}\n")
    x(f"mkdir -p secretos && cat > .sops.yaml <<'EOF'\n{sops_yaml}EOF\ncat > secretos/prod.yaml <<'EOF'\n{SECRETOS}EOF")
    anota(".sops.yaml", "cat .sops.yaml", x("cat .sops.yaml"))
    anota("el archivo en claro", "cat secretos/prod.yaml", x("cat secretos/prod.yaml"))
    anota("cifrar", "sops encrypt -i secretos/prod.yaml", x("sops encrypt -i secretos/prod.yaml && echo codigo=$?", YO))
    anota("el archivo cifrado", "cat secretos/prod.yaml", x("cat secretos/prod.yaml"))
    x("git add -A && git commit -qm 'secretos de producción, cifrados'")
    anota("¿está el secreto en git?", "git grep -c 's3cr3t0' ; git grep -n 'tok_live'",
          x("git grep -c 's3cr3t0'; echo codigo=$?; git grep -n 'tok_live'; echo codigo=$?"))

    salida.append("\n## 3 · Descifrar: con la clave y sin ella")
    anota("con mi clave", "sops decrypt secretos/prod.yaml", x("sops decrypt secretos/prod.yaml", YO))
    anota("un solo valor", "sops decrypt --extract '[\"db\"][\"password\"]' secretos/prod.yaml",
          x("sops decrypt --extract '[\"db\"][\"password\"]' secretos/prod.yaml", YO))
    anota("sin la clave", "sops decrypt secretos/prod.yaml",
          x("sops decrypt secretos/prod.yaml; echo codigo=$?", NADIE))

    salida.append("\n## 4 · Cambiar un valor y el diff en git")
    anota("sops set", "sops set secretos/prod.yaml '[\"db\"][\"password\"]' '\"otra-clave-2026\"'",
          x("sops set secretos/prod.yaml '[\"db\"][\"password\"]' '\"otra-clave-2026\"' && echo codigo=$?", YO))
    anota("git diff", "git diff --stat; git diff", x("git diff --stat; git diff | head -40"))
    x("git commit -qam 'rotar la contraseña de la base de datos'")
    anota("cambiar un dato NO secreto", "sops set ... '[\"db\"][\"host\"]' '\"db2.interna\"'; git diff",
          x("sops set secretos/prod.yaml '[\"db\"][\"host\"]' '\"db2.interna\"' && git diff | grep '^[-+] '", YO))
    x("git commit -qam 'mover la base de datos'")

    salida.append("\n## 5 · Alguien toca el archivo a mano")
    x("cp secretos/prod.yaml /tmp/bueno.yaml && sed -i 's/port: 5432/port: 6543/' secretos/prod.yaml")
    anota("cambiar el puerto con sed (sin sops)", "sed -i 's/port: 5432/port: 6543/' secretos/prod.yaml; git diff",
          x("git diff | grep '^[-+] '"))
    anota("descifrar el archivo tocado", "sops decrypt secretos/prod.yaml",
          x("sops decrypt secretos/prod.yaml; echo codigo=$?", YO))
    x("cp /tmp/bueno.yaml secretos/prod.yaml")

    salida.append("\n## 6 · Una compañera: añadir su clave")
    anota("ella intenta descifrar", "sops decrypt secretos/prod.yaml (con su clave)",
          x("sops decrypt secretos/prod.yaml > /tmp/s 2>&1; c=$?; tail -3 /tmp/s; echo codigo=$c", ELLA))
    x(f"sed -i 's|    age: {pub_yo}|    age: {pub_yo},{pub_ella}|' .sops.yaml")
    anota(".sops.yaml con dos destinatarios", "cat .sops.yaml", x("cat .sops.yaml"))
    anota("sops updatekeys", "sops updatekeys -y secretos/prod.yaml",
          x("sops updatekeys -y secretos/prod.yaml 2>&1", YO))
    anota("ahora sí", "sops decrypt --extract '[\"api\"][\"token\"]' secretos/prod.yaml (con su clave)",
          x("sops decrypt --extract '[\"api\"][\"token\"]' secretos/prod.yaml", ELLA))
    anota("los destinatarios en el archivo", "yq '.sops.age[].recipient' secretos/prod.yaml",
          x("yq '.sops.age[].recipient' secretos/prod.yaml"))

    salida.append("\n## 7 · Llevarlo a la aplicación sin escribirlo en disco")
    x("cat > app.sh <<'EOF'\necho \"conectando a $DB_HOST con la contraseña de ${#DB_PASSWORD} caracteres\"\nEOF")
    x("printf 'DB_HOST=db2.interna\\nDB_PASSWORD=otra-clave-2026\\n' > secretos/app.env")
    anota("cifrar un .env pasando la clave a mano", f"sops encrypt --age {pub_yo[:12]}… -i secretos/app.env",
          x(f"sops encrypt --age {pub_yo} -i secretos/app.env; echo codigo=$?", YO))
    x(f"cat >> .sops.yaml <<'EOF'\n  - path_regex: secretos/.*\\.env$\n    age: {pub_yo},{pub_ella}\nEOF")
    anota("una regla para los .env", "cat .sops.yaml", x("cat .sops.yaml"))
    anota("ahora sí", "sops encrypt -i secretos/app.env",
          x("sops encrypt -i secretos/app.env; echo codigo=$?", YO))
    anota("app.env cifrado (formato dotenv)", "cat secretos/app.env", x("cat secretos/app.env"))
    anota("sops exec-env", "sops exec-env secretos/app.env 'bash app.sh'",
          x("sops exec-env secretos/app.env 'bash app.sh'", YO))
    anota("¿quedó algo en disco?", "ls; env | grep DB_",
          x("ls; env | grep DB_; echo codigo=$?"))

    salida.append("\n## 8 · Rotar la clave de datos")
    anota("antes", "yq '.sops.lastmodified' secretos/prod.yaml; grep -c ENC",
          x("yq '.sops.lastmodified' secretos/prod.yaml; grep -o 'ENC\\[AES256_GCM,data:[^,]*' secretos/prod.yaml | head -2"))
    anota("sops rotate", "sops rotate -i secretos/prod.yaml", x("sops rotate -i secretos/prod.yaml && echo codigo=$?", YO))
    anota("después: mismo contenido, otro cifrado", "grep -o 'ENC[...' secretos/prod.yaml",
          x("grep -o 'ENC\\[AES256_GCM,data:[^,]*' secretos/prod.yaml | head -2; sops decrypt --extract '[\"db\"][\"password\"]' secretos/prod.yaml", YO))
    anota("historial", "git log --oneline", x("git log --oneline"))

    sh(["docker", "rm", "-f", C])
    cab = ["# SALIDA — SOPS (vídeo 330)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           "Imagen ghcr.io/getsops/sops:v3.13.3-alpine + age."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
