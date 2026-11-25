# -*- coding: utf-8 -*-
"""lecciones.py — el «navegador» del curso: corre DENTRO de la red de Docker (imagen curso-forja-cliente:1).

Lo lanza ejecutar_todo.py por fases, porque entre una y otra hay que reiniciar Forgejo con otra
configuración:

    python lecciones.py A    Forgejo recién instalado, configuración por defecto
    python lecciones.py B    Forgejo con ROOT_URL y el registro cerrado; prepara la app OAuth
    python lecciones.py C    Woodpecker: login por OAuth, activar el repositorio, primer push
    python lecciones.py D    Forgejo ya deja llamar a Woodpecker; el pipeline y el secreto

Imprime cada apartado con «== N.M · título ==» y guarda lo que necesita la fase siguiente en
estado.json (tokens de laboratorio que se borran al terminar).
"""
import base64
import json
import re
import sys
import time
from pathlib import Path

import requests

FJ = "http://forgejo:3000"
WP = "http://woodpecker:8000"
CLAVE = "Clave-de-laboratorio-1"
ESTADO = Path("/curso/estado.json")


def titulo(t):
    print(f"\n== {t} ==")


def estado():
    return json.loads(ESTADO.read_text()) if ESTADO.exists() else {}


def guardar(**kw):
    e = estado()
    e.update(kw)
    ESTADO.write_text(json.dumps(e))


def csrf(html):
    m = re.search(r'name="_csrf" value="([^"]+)"', html)
    return m.group(1) if m else None


def registrar(usuario):
    """Rellena el formulario de alta de Forgejo como lo haría cualquiera con un navegador."""
    s = requests.Session()
    r = s.get(f"{FJ}/user/sign_up")
    token = csrf(r.text)
    aviso = ""
    if 'name="user_name"' not in r.text:
        m = re.search(r"(?i)[^<>]*registration[^<>]*", r.text)
        aviso = f"la página dice «{m.group(0).strip() if m else 'sin formulario'}»; "
    # Se envía el formulario igualmente: lo que importa es lo que hace el servidor, no la página.
    r = s.post(f"{FJ}/user/sign_up", allow_redirects=False, data={
        "_csrf": token or "", "user_name": usuario, "email": f"{usuario}@ejemplo.test",
        "password": CLAVE, "retype": CLAVE})
    destino = r.headers.get("Location")
    return r.status_code, aviso + (f"redirige a {destino}" if destino else "el servidor lo rechaza")


def api(metodo, ruta, usuario="duena", **kw):
    return requests.request(metodo, f"{FJ}/api/v1{ruta}", auth=(usuario, CLAVE), **kw)


def crear_repo():
    r = api("POST", "/user/repos", json={"name": "tienda", "auto_init": True, "default_branch": "main"})
    assert r.status_code in (201, 409), r.text
    return api("GET", "/repos/duena/tienda").json()


# ═══════════════════════════════════════════════════════════════════════════════════════════
def fase_a():
    titulo("1.1 · Un Forgejo recién instalado. Se registra el primero que llega")
    for u in ("intruso", "duena"):
        codigo, res = registrar(u)
        info = api("GET", "/user", usuario=u).json()
        print(f"  alta de «{u}»: HTTP {codigo}, {res} · is_admin: {info.get('is_admin')}")
    print("  el primero en registrarse es administrador: si la instancia está en internet, gana quien llegue antes")

    titulo("2.1 · El registro, abierto por defecto")
    codigo, res = registrar("cualquiera")
    print(f"  alta de «cualquiera», sin invitación: HTTP {codigo}, {res}")
    total = len(api("GET", "/admin/users", usuario="intruso").json())
    print(f"  usuarios en la instancia: {total}")

    titulo("3.1 · La URL de clonado, con ROOT_URL sin tocar")
    repo = crear_repo()
    print(f"  clone_url: {repo['clone_url']}")
    print("  es la que Forgejo enseña en la web y manda a Woodpecker: desde otra máquina, localhost es ella misma")


def fase_b():
    titulo("2.2 · Lo correcto: DISABLE_REGISTRATION=true (y el administrador, creado por consola)")
    codigo, res = registrar("cualquiera")
    print(f"  alta de «cualquiera»: HTTP {codigo} · {res}")
    print(f"  ¿existe «cualquiera»?: {requests.get(f'{FJ}/api/v1/users/cualquiera').status_code == 200}")

    titulo("3.2 · Lo correcto: ROOT_URL con la dirección por la que se llega de verdad")
    repo = crear_repo()
    print(f"  clone_url: {repo['clone_url']}")

    r = api("POST", "/user/applications/oauth2", json={
        "name": "woodpecker", "redirect_uris": [f"{WP}/authorize"], "confidential_client": True})
    assert r.status_code == 201, r.text
    guardar(cliente=r.json()["client_id"], secreto=r.json()["client_secret"])


def entrar_en_woodpecker():
    """El login de Woodpecker es OAuth contra Forgejo: aquí se hace a mano, formulario a formulario."""
    s = requests.Session()
    r = s.get(f"{FJ}/user/login")
    s.post(f"{FJ}/user/login", data={"_csrf": csrf(r.text), "user_name": "duena", "password": CLAVE})
    r = s.get(f"{WP}/authorize")                      # -> Forgejo: «¿autorizas a woodpecker?»
    if "/login/oauth/grant" in r.text:
        datos = dict(re.findall(r'name="(\w+)" value="([^"]*)"', r.text))
        datos["granted"] = "true"
        r = s.post(f"{FJ}/login/oauth/grant", data=datos)  # -> vuelve a Woodpecker con el código
    cfg = s.get(f"{WP}/web-config.js").text
    token_csrf = re.search(r'WOODPECKER_CSRF\s*=\s*"([^"]+)"', cfg).group(1)
    r = s.post(f"{WP}/api/user/token", headers={"X-CSRF-TOKEN": token_csrf})
    assert r.ok and r.text, f"login de Woodpecker: {r.status_code} {r.text[:200]}"
    return r.text.strip()


def wp(metodo, ruta, **kw):
    return requests.request(metodo, f"{WP}/api{ruta}",
                            headers={"Authorization": f"Bearer {estado()['wp_token']}"}, **kw)


def subir(ruta, contenido, mensaje):
    """Un commit por la API de Forgejo: dispara el webhook de push igual que un git push."""
    actual = api("GET", f"/repos/duena/tienda/contents/{ruta}")
    datos = {"content": base64.b64encode(contenido.encode()).decode(), "message": mensaje, "branch": "main"}
    if actual.status_code == 200:
        datos["sha"] = actual.json()["sha"]
        r = api("PUT", f"/repos/duena/tienda/contents/{ruta}", json=datos)
    else:
        r = api("POST", f"/repos/duena/tienda/contents/{ruta}", json=datos)
    assert r.status_code in (200, 201), r.text


def pipelines():
    return wp("GET", f"/repos/{estado()['repo_wp']}/pipelines").json() or []


PIPELINE = """steps:
  - name: pruebas
    image: alpine:3.22
    commands:
      - echo "pruebas de la tienda, todo bien"
"""


def fase_c():
    guardar(wp_token=entrar_en_woodpecker())
    titulo("4.1 · Woodpecker: entrar con la cuenta de Forgejo y activar el repositorio")
    repos = wp("GET", "/user/repos?all=true").json()
    remoto = next(r for r in repos if r["full_name"] == "duena/tienda")
    r = wp("POST", f"/repos?forge_remote_id={remoto['forge_remote_id']}")
    assert r.ok, r.text
    guardar(repo_wp=r.json()["id"])
    print(f"  login por OAuth: hecho · repositorio duena/tienda activado en Woodpecker (HTTP {r.status_code})")
    ganchos = api("GET", "/repos/duena/tienda/hooks").json()
    print(f"  webhooks en Forgejo: {len(ganchos)} · apunta a {ganchos[0]['config']['url'].split('?')[0]}")

    titulo("4.2 · La trampa: el primer push, y el pipeline que nunca llega")
    subir(".woodpecker.yaml", PIPELINE, "ci: primer pipeline")
    time.sleep(20)
    print(f"  push hecho · 20 s después, pipelines en Woodpecker: {len(pipelines())}")
    print("  ni Woodpecker ni el push dan error: el webhook se queda en Forgejo")


def esperar_pipeline(minimo, segundos=120):
    for _ in range(segundos):
        ps = pipelines()
        if len(ps) >= minimo and ps[0]["status"] not in ("pending", "running"):
            return ps[0]
        time.sleep(1)
    return pipelines()[0] if pipelines() else None


def lineas_de(numero, paso):
    p = wp("GET", f"/repos/{estado()['repo_wp']}/pipelines/{numero}").json()
    pasos = [s for w in p.get("workflows", []) for s in w.get("children", [])]
    st = next((s for s in pasos if s["name"] == paso), None)
    if st is None:
        errores = [e.get("message", e) for e in (p.get("errors") or [])]
        return [f"(no hay paso «{paso}»; errores del pipeline: {errores}; pasos: {[s['name'] for s in pasos]})"]
    # El estado «success» puede llegar antes que el log: se reintenta unos segundos.
    for _ in range(20):
        logs = wp("GET", f"/repos/{estado()['repo_wp']}/logs/{numero}/{st['id']}").json() or []
        lineas = [base64.b64decode(l["data"]).decode(errors="replace").rstrip() for l in logs if l.get("data")]
        if lineas:
            return lineas
        time.sleep(1)
    return [f"(el paso «{paso}» terminó, pero Woodpecker no devolvió su log en 20 s)"]


def fase_d():
    titulo("4.3 · Lo correcto: ALLOWED_HOST_LIST con la red de Woodpecker, y otro push")
    subir("LEEME.md", "# tienda\n", "docs: el primer commit que sí llega")
    p = esperar_pipeline(1)
    print(f"  pipeline #{p['number']} · evento {p['event']} · estado {p['status']}")
    for l in lineas_de(p["number"], "pruebas"):
        print(f"    {l}")

    titulo("5.1 · Un secreto en Woodpecker, y el log que lo tapa")
    r = wp("POST", f"/repos/{estado()['repo_wp']}/secrets", json={
        "name": "clave_pagos", "value": "la-de-los-pagos", "events": ["push"]})
    assert r.ok, r.text
    subir(".woodpecker.yaml", """steps:
  - name: desplegar
    image: alpine:3.22
    environment:
      CLAVE:
        from_secret: clave_pagos
    commands:
      - echo "la clave es $CLAVE"
      - echo "$CLAVE" | base64
      - echo "$CLAVE" | rev
""", "ci: desplegar con la clave de los pagos")
    p = esperar_pipeline(2)
    print(f"  pipeline #{p['number']} · estado {p['status']}")
    for l in lineas_de(p["number"], "desplegar"):
        print(f"    {l}")
    print("  el log solo tapa el texto exacto: en base64 o al revés, la clave sale entera")

    titulo("5.2 · Lo correcto: el secreto, solo para la imagen que lo necesita")
    r = wp("PATCH", f"/repos/{estado()['repo_wp']}/secrets/clave_pagos", json={
        "name": "clave_pagos", "value": "la-de-los-pagos", "events": ["push"],
        "images": ["woodpeckerci/plugin-docker-buildx"]})
    assert r.ok, r.text
    print(f"  clave_pagos limitada a la imagen: {r.json().get('images')}")
    subir("LEEME.md", "# tienda\n\nOtra vez el mismo pipeline.\n", "docs: otro push, el mismo paso con alpine")
    p = esperar_pipeline(3)
    print(f"  pipeline #{p['number']} · estado {p['status']}")
    detalle = wp("GET", f"/repos/{estado()['repo_wp']}/pipelines/{p['number']}").json()
    for e in detalle.get("errors") or []:
        if "secret" in e.get("message", ""):
            print(f"    {e['message']}")
    pasos = [s for w in detalle.get("workflows", []) for s in w.get("children", [])]
    print(f"  pasos que llegaron a ejecutarse: {len(pasos)}")
    print("  el paso con alpine ya no recibe la clave: ni siquiera arranca")


if __name__ == "__main__":
    {"A": fase_a, "B": fase_b, "C": fase_c, "D": fase_d}[sys.argv[1]]()
