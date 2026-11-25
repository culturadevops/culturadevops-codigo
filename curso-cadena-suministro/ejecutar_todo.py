# -*- coding: utf-8 -*-
"""ejecutar_todo.py — corre el curso «Cadena de suministro» de principio a fin y escribe SALIDA.md.

Todo en Docker, en esta máquina:
  · un registro propio (registry:3) en localhost:5000, también conectado a la red «cadena-interna»;
  · «cadena-interna» es una red --internal: SIN salida a internet. cosign y el intruso corren ahí,
    así que ninguna firma puede acabar en Rekor (el registro público de transparencia de Sigstore,
    que es permanente). Solo Trivy sale a internet, y solo para bajar su base de datos;
  · las claves de cosign se generan en cada ejecución en claves/ (en .gitignore) con una frase de
    paso de laboratorio. No sirven para nada fuera de este curso.

    python ejecutar_todo.py
"""
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
BASH = r"C:\Program Files\Git\bin\bash.exe"
RED = "cadena-interna"
REG = "localhost:5000"           # el registro, visto desde esta máquina
REG_DENTRO = "registro:5000"     # el mismo registro, visto desde la red interna

TRIVY = "aquasec/trivy:0.75.0"
COSIGN = "ghcr.io/sigstore/cosign/cosign:v3.1.3"
SYFT = "anchore/syft:v1.54.1"
CRANE = "gcr.io/go-containerregistry/crane:latest"
REGISTRY = "registry:3"
CLAVE = "curso-solo-local"       # la frase de paso de la clave de laboratorio

SOCK = ["-v", "//var/run/docker.sock:/var/run/docker.sock"]
CACHE_TRIVY = ["-v", "trivy-cache:/root/.cache/trivy"]
salida = []


def p(t=""):
    print(t)
    salida.append(t)


def titulo(t):
    p("")
    p(f"== {t} ==")


def run(args, entrada=None):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=ENV, input=entrada)
    return r.returncode, (r.stdout + r.stderr).strip()


def docker(*a):
    return run(["docker", *a])


def mostrar(cmd, codigo, out, filtro=None, maximo=8):
    """Imprime el comando como se teclearía y las líneas de su salida (las que pasan el filtro)."""
    p(f"$ {cmd}")
    lineas = [l for l in out.splitlines() if l.strip()]
    if filtro:
        lineas = [l for l in lineas if re.search(filtro, l)]
    for l in lineas[:maximo]:
        p("  " + l.rstrip())
    p(f"  (código de salida {codigo})")


def construir(etiqueta, version):
    c, o = docker("build", "-q", "-t", f"{REG}/{etiqueta}", "--build-arg", f"VERSION={version}", str(AQUI / "app"))
    assert c == 0, o
    c, o = docker("push", "-q", f"{REG}/{etiqueta}")
    assert c == 0, o
    return digest(etiqueta)


def digest(etiqueta):
    """El digest que tiene AHORA la etiqueta en el registro (no lo que hay en la caché local)."""
    c, o = docker("buildx", "imagetools", "inspect", f"{REG}/{etiqueta}", "--format", "{{json .Manifest.Digest}}")
    assert c == 0, o
    return o.strip().strip('"')


def corto(d):
    return d[:19] + "..."


def cosign(*a):
    clv = (AQUI / "claves").as_posix()
    return run(["docker", "run", "--rm", "--network", RED, "-v", f"{clv}:/claves", "-w", "/claves",
                "-e", f"COSIGN_PASSWORD={CLAVE}", COSIGN, *a])


def trivy(*a):
    return run(["docker", "run", "--rm", *SOCK, *CACHE_TRIVY, TRIVY, *a])


def preparar():
    for n in ("registro", "registro-auth"):
        docker("rm", "-f", n)
    docker("network", "rm", RED)
    docker("network", "create", "--internal", RED)
    docker("run", "-d", "--name", "registro", "-p", "127.0.0.1:5000:5000", REGISTRY)
    docker("network", "connect", RED, "registro")
    (AQUI / "claves").mkdir(exist_ok=True)
    for f in (AQUI / "claves").glob("cosign.*"):
        f.unlink()
    c, o = cosign("generate-key-pair")
    assert c == 0, o
    c, o = run(["docker", "run", "--rm", "--network", RED, "alpine:3.22", "sh", "-c",
                "wget -q -T 3 -O /dev/null https://rekor.sigstore.dev 2>/dev/null && echo SI || echo NO"])
    assert o.strip() == "NO", f"la red interna tiene salida a internet ({o!r}): no sigo"
    trivy("image", "--download-db-only", "--quiet")


def limpiar():
    for n in ("registro", "registro-auth"):
        docker("rm", "-f", n)
    docker("network", "rm", RED)


# ═══════════════════════════════════════════════════════════════════════════════════════════
def leccion_1():
    titulo("1.1 · Se sube la tienda 1.0")
    d1 = construir("tienda:1.0", "1.0")
    p(f"  {REG}/tienda:1.0 -> {corto(d1)}")
    c, o = docker("run", "--rm", f"{REG}/tienda:1.0")
    mostrar(f"docker run {REG}/tienda:1.0", c, o)

    titulo("1.2 · La trampa: alguien sube otra imagen con la misma etiqueta")
    d2 = construir("tienda:1.0", "1.0 (cambiada)")
    p(f"  docker push no preguntó nada. {REG}/tienda:1.0 -> {corto(d2)}")
    docker("rmi", f"{REG}/tienda:1.0")
    docker("pull", "-q", f"{REG}/tienda:1.0")
    c, o = docker("run", "--rm", f"{REG}/tienda:1.0")
    mostrar(f"docker run {REG}/tienda:1.0", c, o)
    p("  la misma etiqueta, otra imagen, y ningún error")

    titulo("1.3 · Lo correcto: desplegar por digest")
    docker("pull", "-q", f"{REG}/tienda@{d1}")
    c, o = docker("run", "--rm", f"{REG}/tienda@{d1}")
    mostrar(f"docker run {REG}/tienda@{corto(d1)}", c, o)
    p("  un digest es el hash del contenido: no se puede mover")


def leccion_2():
    titulo("2.1 · Trivy contra una imagen vieja (alpine:3.14.0)")
    c, o = trivy("image", "--quiet", "--skip-db-update", "--scanners", "vuln", "alpine:3.14.0")
    mostrar("trivy image alpine:3.14.0", c, o, filtro=r"^Total")
    m = re.search(r"Total: (\d+) .*CRITICAL: (\d+)", o)
    p(f"  {m.group(1)} vulnerabilidades, {m.group(2)} críticas... y código {c}: en un pipeline, este paso sale en verde")

    titulo("2.2 · Lo correcto: --exit-code 1 para lo que no se acepta")
    c, o = trivy("image", "--quiet", "--skip-db-update", "--scanners", "vuln", "--exit-code", "1",
                 "--severity", "CRITICAL", "alpine:3.14.0")
    mostrar("trivy image --exit-code 1 --severity CRITICAL alpine:3.14.0", c, o, filtro=r"^Total")

    titulo("2.3 · Y la imagen de la tienda, con su base de hoy (alpine:3.22)")
    c, o = trivy("image", "--quiet", "--skip-db-update", "--scanners", "vuln", f"{REG}/tienda:1.0")
    mostrar(f"trivy image {REG}/tienda:1.0", c, o, filtro=r"^Total|^│ .*alpine")
    c, o = trivy("image", "--quiet", "--skip-db-update", "--scanners", "vuln", "--exit-code", "1",
                 "--severity", "CRITICAL", f"{REG}/tienda:1.0")
    mostrar(f"trivy image --exit-code 1 --severity CRITICAL {REG}/tienda:1.0", c, o, filtro=r"^Total")
    c, o = trivy("--version")
    fecha = re.search(r"UpdatedAt: (\S+)", o)
    p(f"  base de datos de Trivy del {fecha.group(1) if fecha else '?'}: mañana el resultado puede ser otro")


def por_paquete(fichero):
    """Cuenta las vulnerabilidades de un informe JSON de Trivy, por paquete."""
    import json
    from collections import Counter
    d = json.loads(fichero.read_text(encoding="utf-8"))
    c = Counter()
    for r in d.get("Results", []):
        for v in r.get("Vulnerabilities") or []:
            c[v["PkgName"]] += 1
    return c


def leccion_3():
    sbom = AQUI / "sbom"
    sbom.mkdir(exist_ok=True)
    vol = ["-v", f"{sbom.as_posix()}:/sbom"]

    def escanear(nombre):
        c, o = run(["docker", "run", "--rm", *CACHE_TRIVY, *vol, TRIVY, "sbom", "--skip-db-update",
                    "--format", "json", "--output", f"/sbom/informe-{nombre}", f"/sbom/{nombre}"])
        assert c == 0, o
        return o, por_paquete(sbom / f"informe-{nombre}")

    c, o = run(["docker", "run", "--rm", *SOCK, *CACHE_TRIVY, *vol, TRIVY, "image", "--quiet", "--skip-db-update",
                "--scanners", "vuln", "--format", "json", "--output", "/sbom/informe-imagen.json", "alpine:3.14.0"])
    assert c == 0, o
    imagen = sum(por_paquete(sbom / "informe-imagen.json").values())

    titulo("3.1 · El SBOM: la lista de lo que lleva la imagen (syft)")
    c, o = run(["docker", "run", "--rm", *SOCK, *vol, SYFT,
                "alpine:3.14.0", "-o", "cyclonedx-json=/sbom/syft.cdx.json", "-q"])
    assert c == 0, o
    import json
    datos = json.loads((sbom / "syft.cdx.json").read_text(encoding="utf-8"))
    comps = [x for x in datos.get("components", []) if x.get("type") == "library"]
    p("$ syft alpine:3.14.0 -o cyclonedx-json=syft.cdx.json")
    p(f"  {len(comps)} paquetes: " + ", ".join(f"{x['name']} {x.get('version', '')}" for x in comps[:4]) + ", ...")

    titulo("3.2 · La trampa: Trivy escanea el SBOM de syft")
    log, syft = escanear("syft.cdx.json")
    p("$ trivy sbom syft.cdx.json")
    for l in log.splitlines():
        if "WARN" in l:
            p("  " + l.split("WARN", 1)[1].strip())
    p(f"  vulnerabilidades: {sum(syft.values())} · escaneando la imagen eran {imagen} · y sin ningún error")

    titulo("3.3 · Lo que falta, y por qué")
    c, o = run(["docker", "run", "--rm", *SOCK, *CACHE_TRIVY, *vol, TRIVY, "image", "--quiet", "--skip-db-update",
                "--format", "cyclonedx", "--output", "/sbom/trivy.cdx.json", "alpine:3.14.0"])
    assert c == 0, o
    _, propio = escanear("trivy.cdx.json")
    faltan = {k: v for k, v in propio.items() if syft.get(k, 0) < v}
    for k, v in sorted(faltan.items()):
        p(f"  {k:<14} {v:>3} vulnerabilidades que el SBOM de syft no destapa")
    origen = {}
    for x in json.loads((sbom / "trivy.cdx.json").read_text(encoding="utf-8")).get("components", []):
        for prop in x.get("properties", []):
            if prop["name"] == "aquasecurity:trivy:SrcName":
                origen[x["name"]] = prop["value"]
    p("  sus paquetes de origen: " + ", ".join(f"{k} -> {origen.get(k, '?')}" for k in sorted(faltan)))
    p("  Trivy busca por paquete de origen; syft lo guarda en su propio campo (syft:metadata:originPackage)")

    titulo("3.4 · Lo correcto: el SBOM de la misma herramienta que lo va a escanear")
    p("$ trivy image --format cyclonedx --output trivy.cdx.json alpine:3.14.0 && trivy sbom trivy.cdx.json")
    p(f"  vulnerabilidades: {sum(propio.values())} · escaneando la imagen: {imagen} · ¿iguales?: {sum(propio.values()) == imagen}")
    p("  y el día que salga un CVE nuevo, se vuelve a escanear el SBOM guardado, sin bajar la imagen")


def leccion_4():
    titulo("4.1 · Firmar la tienda 2.0 con cosign (por digest)")
    d = construir("tienda:2.0", "2.0")
    c, o = cosign("sign", "--yes", "--key", "/claves/cosign.key", "--allow-http-registry",
                  "--use-signing-config=false", "--tlog-upload=false", f"{REG_DENTRO}/tienda@{d}")
    mostrar(f"cosign sign --key cosign.key {REG_DENTRO}/tienda@{corto(d)}", c, o, filtro=r"Pushing|Error")
    c, o = cosign("verify", "--key", "/claves/cosign.pub", "--allow-http-registry",
                  "--insecure-ignore-tlog=true", f"{REG_DENTRO}/tienda:2.0")
    mostrar(f"cosign verify --key cosign.pub {REG_DENTRO}/tienda:2.0", c, o,
            filtro=r"signatures were verified|Error")

    titulo("4.2 · La trampa: la etiqueta se mueve a una imagen sin firmar")
    construir("tienda:2.0", "2.0 (sin firmar)")
    c, o = cosign("verify", "--key", "/claves/cosign.pub", "--allow-http-registry",
                  "--insecure-ignore-tlog=true", f"{REG_DENTRO}/tienda:2.0")
    mostrar(f"cosign verify --key cosign.pub {REG_DENTRO}/tienda:2.0", c, o, filtro=r"[Ee]rror", maximo=1)
    docker("pull", "-q", f"{REG}/tienda:2.0")
    c, o = docker("run", "--rm", f"{REG}/tienda:2.0")
    mostrar(f"docker run {REG}/tienda:2.0", c, o)
    p("  cosign dice que la imagen nueva no está firmada... pero docker run no le pregunta: se ejecuta igual")


def leccion_5():
    titulo("5.1 · desplegar.sh con una imagen firmada")
    d = construir("tienda:3.0", "3.0")
    cosign("sign", "--yes", "--key", "/claves/cosign.key", "--allow-http-registry",
           "--use-signing-config=false", "--tlog-upload=false", f"{REG_DENTRO}/tienda@{d}")
    c, o = run([BASH, "-c", f"cd '{AQUI.as_posix()}' && sh desplegar.sh tienda:3.0"])
    mostrar("./desplegar.sh tienda:3.0", c, o)

    titulo("5.2 · desplegar.sh con la etiqueta movida a una imagen sin firmar")
    construir("tienda:3.0", "3.0 (sin firmar)")
    c, o = run([BASH, "-c", f"cd '{AQUI.as_posix()}' && sh desplegar.sh tienda:3.0"])
    mostrar("./desplegar.sh tienda:3.0", c, o)


def leccion_6():
    titulo("6.1 · La trampa: el registro sin autenticación")
    c, o = run(["docker", "run", "--rm", "--network", RED, CRANE, "catalog", "--insecure", REG_DENTRO])
    mostrar(f"crane catalog {REG_DENTRO}   (desde otro contenedor de la red, sin credenciales)", c, o)
    antes = digest("tienda:1.0")
    c, o = run(["docker", "run", "--rm", "--network", RED, CRANE, "copy", "--insecure",
                f"{REG_DENTRO}/tienda:2.0", f"{REG_DENTRO}/tienda:1.0"])
    p(f"$ crane copy {REG_DENTRO}/tienda:2.0 {REG_DENTRO}/tienda:1.0")
    p(f"  (código de salida {c})")
    despues = digest("tienda:1.0")
    p(f"  tienda:1.0 antes: {corto(antes)} · después: {corto(despues)} · ¿cambió?: {antes != despues}")
    p("  cualquiera que llegue al puerto puede leer, subir y sobrescribir etiquetas")

    titulo("6.2 · Lo correcto: el registro con usuario y contraseña (htpasswd)")
    authd = AQUI / "registro-auth"
    authd.mkdir(exist_ok=True)
    c, o = docker("run", "--rm", "httpd:2.4-alpine", "htpasswd", "-Bbn", "ci", "clave-de-laboratorio")
    (authd / "htpasswd").write_bytes((o.strip() + "\n").encode("utf-8"))
    docker("run", "-d", "--name", "registro-auth", "--network", RED,
           "-v", f"{authd.as_posix()}:/auth:ro",
           "-e", "REGISTRY_AUTH=htpasswd", "-e", "REGISTRY_AUTH_HTPASSWD_REALM=curso",
           "-e", "REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd", REGISTRY)
    c, o = run(["docker", "run", "--rm", "--network", RED, CRANE, "catalog", "--insecure", "registro-auth:5000"])
    mostrar("crane catalog registro-auth:5000   (sin credenciales)", c, o, maximo=1)
    c, o = run(["docker", "run", "--rm", "--network", RED, "--entrypoint", "sh", CRANE.replace(":latest", ":debug"), "-c",
                "crane auth login registro-auth:5000 -u ci -p clave-de-laboratorio --insecure >/dev/null 2>&1; "
                "crane catalog --insecure registro-auth:5000 && echo vacío, pero dentro"])
    mostrar("crane auth login registro-auth:5000 -u ci ... && crane catalog registro-auth:5000", c, o, maximo=2)
    p("  ojo: por HTTP la contraseña viaja en claro. Con usuario, siempre detrás de TLS")


def main():
    for imagen in (TRIVY, COSIGN, SYFT, CRANE, CRANE.replace(":latest", ":debug"), REGISTRY,
                   "httpd:2.4-alpine", "alpine:3.14.0", "alpine:3.22"):
        docker("pull", "-q", imagen)
    preparar()
    cabecera = ["# SALIDA — curso «Cadena de suministro: Trivy, firmas con cosign y registro propio»", "",
                "> Generado por `ejecutar_todo.py`. **No se escribe a mano.**", "",
                f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`"]
    for nombre, args in (("trivy", ["docker", "run", "--rm", TRIVY, "--version"]),
                         ("cosign", ["docker", "run", "--rm", COSIGN, "version"]),
                         ("syft", ["docker", "run", "--rm", SYFT, "version"]),
                         ("registry", ["docker", "run", "--rm", REGISTRY, "--version"])):
        _, o = run(args)
        v = re.search(r"(?:Version|GitVersion|registry \S+)\s*:?\s*(v?\d[\w.\-]*)", o)
        cabecera.append(f"- {nombre}: `{v.group(1) if v else o.splitlines()[0]}`")
    _, o = docker("version", "--format", "{{.Server.Version}}")
    cabecera.append(f"- Docker `{o.strip()}`")
    fallos = 0
    try:
        for n, f in enumerate((leccion_1, leccion_2, leccion_3, leccion_4, leccion_5, leccion_6), 1):
            salida.append(f"\n## Leccion {n}\n\n```")
            try:
                f()
            except AssertionError as e:
                p(f"  [X] fallo del banco de pruebas: {e}")
                fallos += 1
            salida.append("```")
    finally:
        limpiar()
    texto = "\n".join(cabecera) + "\n" + "\n".join(salida) + "\n"
    (AQUI / "SALIDA.md").write_bytes(texto.encode("utf-8"))
    print(f"\n[{'ok' if not fallos else 'X'}] SALIDA.md · {fallos} fallos del banco")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
