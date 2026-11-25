# -*- coding: utf-8 -*-
"""Demo del vídeo 802 (cultura-devops): inyección SQL, XSS con Jinja2 y path traversal, en Python.

Se ejecuta SOLO dentro del contenedor (ver correr.sh). Todo vive en un directorio temporal creado aquí;
el «secreto» es un archivo de mentira que crea la propia demo. No toca nada fuera de ese directorio.
Uso:  python demo.py sql | xss | ruta | todo
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path


def titulo(t):
    print(f"\n### {t}")


# ═══════════════ 1 · INYECCIÓN SQL ═══════════════
def base_sql():
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, usuario TEXT, clave TEXT, nombre TEXT);
        INSERT INTO usuarios VALUES (1, 'admin', 'clave-falsa-9f2', 'Administración');
        INSERT INTO usuarios VALUES (2, 'ana', 'gato123', 'Ana');
        CREATE TABLE tarjetas (usuario_id INTEGER, numero TEXT);
        INSERT INTO tarjetas VALUES (1, '4000-0000-0000-0001 (FALSA)');
        INSERT INTO tarjetas VALUES (2, '4000-0000-0000-0002 (FALSA)');
        CREATE TABLE productos (id INTEGER PRIMARY KEY, nombre TEXT);
        INSERT INTO productos VALUES (1, 'teclado'), (2, 'monitor');
    """)
    return con


def login_fstring(con, usuario, clave):
    sql = f"SELECT nombre FROM usuarios WHERE usuario = '{usuario}' AND clave = '{clave}'"
    print(f"  consulta: {sql}")
    fila = con.execute(sql).fetchone()
    return f"ENTRASTE como {fila[0]}" if fila else "denegado"


def login_param(con, usuario, clave):
    fila = con.execute("SELECT nombre FROM usuarios WHERE usuario = ? AND clave = ?", (usuario, clave)).fetchone()
    return f"ENTRASTE como {fila[0]}" if fila else "denegado"


def buscar_fstring(con, texto):
    sql = f"SELECT nombre FROM productos WHERE nombre LIKE '%{texto}%'"
    print(f"  consulta: {sql}")
    return con.execute(sql).fetchall()


def buscar_param(con, texto):
    return con.execute("SELECT nombre FROM productos WHERE nombre LIKE ?", (f"%{texto}%",)).fetchall()


def demo_sql():
    titulo("1 · inyección SQL (sqlite3, Python " + sys.version.split()[0] + ", SQLite " + sqlite3.sqlite_version + ")")
    con = base_sql()
    casos = [("ana", "gato123"), ("ana", "nolase"), ("admin", "' OR '1'='1"), ("admin' --", "cualquiera")]
    for u, c in casos:
        print(f"\nlogin usuario={u!r} clave={c!r}")
        print(f"  A) f-string:   {login_fstring(con, u, c)}")
        print(f"  B) parámetros: {login_param(con, u, c)}")
    for t in ["tecla", "x' UNION SELECT numero FROM tarjetas --"]:
        print(f"\nbuscar {t!r}")
        print(f"  A) f-string:   {buscar_fstring(con, t)}")
        print(f"  B) parámetros: {buscar_param(con, t)}")
    print("\nlo que NO se puede parametrizar: un nombre de columna")
    try:
        con.execute("SELECT nombre FROM productos ORDER BY ?", ("nombre; DROP TABLE productos",)).fetchall()
        print("  ORDER BY ? -> se acepta, pero ordena por un valor fijo, no por la columna")
    except sqlite3.Error as e:
        print(f"  error: {e}")
    permitidas = {"id", "nombre"}
    pedida = "nombre; DROP TABLE productos"
    print(f"  lista blanca: {pedida!r} in {sorted(permitidas)} -> {pedida in permitidas}")


# ═══════════════ 2 · XSS CON JINJA2 ═══════════════
def demo_xss():
    import jinja2
    from markupsafe import Markup, escape
    from jinja2 import Environment, DictLoader, select_autoescape

    titulo("2 · XSS con Jinja2 " + jinja2.__version__)
    plantilla = '<p>{{ comentario }}</p>'
    malo = '<script>robar(document.cookie)</script>'
    print(f"plantilla: {plantilla}")
    print(f"dato:      {malo}")

    e1 = Environment()
    print("\nA) Environment() a secas  autoescape =", e1.autoescape)
    print("  ", e1.from_string(plantilla).render(comentario=malo))

    e2 = Environment(autoescape=True)
    print("\nB) Environment(autoescape=True)")
    print("  ", e2.from_string(plantilla).render(comentario=malo))

    e3 = Environment(loader=DictLoader({"pagina.html": plantilla, "correo.txt": plantilla}),
                     autoescape=select_autoescape(["html", "xml"]))
    print("\nC) select_autoescape(['html', 'xml'])")
    print("   pagina.html:", e3.get_template("pagina.html").render(comentario=malo))
    print("   correo.txt: ", e3.get_template("correo.txt").render(comentario=malo))
    print("   from_string:", e3.from_string(plantilla).render(comentario=malo))

    print("\nD) con autoescape, pero |safe")
    print("  ", e2.from_string('<p>{{ comentario|safe }}</p>').render(comentario=malo))

    print("\nE) con autoescape, pero Markup(dato del usuario)")
    print("  ", e2.from_string(plantilla).render(comentario=Markup(malo)))

    print("\nF) Markup bien usado: tu HTML fijo + el dato escapado")
    print("  ", e2.from_string(plantilla).render(comentario=Markup("<b>{}</b>").format(malo)))

    print("\nG) autoescape no basta en un atributo sin comillas ni en href")
    print("  ", e2.from_string('<a href="{{ web }}">mi web</a>').render(web="javascript:robar()"))
    print("  ", e2.from_string('<img src={{ foto }}>').render(foto="x.png onerror=robar()"))
    print("\nescape() a mano:", escape(malo))


# ═══════════════ 3 · PATH TRAVERSAL ═══════════════
def demo_ruta():
    titulo("3 · path traversal")
    raiz = Path(tempfile.mkdtemp(prefix="demo802-"))
    os.chdir(raiz)
    (raiz / "publico" / "docs").mkdir(parents=True)
    (raiz / "publico" / "leeme.txt").write_text("hola, soy público", encoding="utf-8")
    (raiz / "publico" / "docs" / "manual.txt").write_text("manual en docs", encoding="utf-8")
    (raiz / "secreto.txt").write_text("CLAVE_FALSA_DE_DEMO=1234", encoding="utf-8")
    base = str(raiz / "publico")
    print(f"carpeta temporal: {raiz}")
    print("contenido: publico/leeme.txt  publico/docs/manual.txt  secreto.txt (fuera de publico)")

    def abrir_mal(nombre):
        ruta = os.path.join(base, nombre)
        with open(ruta, encoding="utf-8") as f:
            return f"lee: {f.read()}   (ruta: {ruta})"

    def abrir_bien(nombre):
        b = Path(base).resolve()
        ruta = (b / nombre).resolve()
        if not ruta.is_relative_to(b):
            return f"rechazado: {ruta} queda fuera de {b}"
        return f"lee: {ruta.read_text(encoding='utf-8')}"

    from werkzeug.security import safe_join


    secreto_abs = str(raiz / "secreto.txt")
    print(f"\nos.path.join({base!r}, {secreto_abs!r})\n  -> {os.path.join(base, secreto_abs)!r}")
    print(f"Path({base!r}) / {secreto_abs!r}\n  -> {str(Path(base) / secreto_abs)!r}")

    for nombre in ["leeme.txt", "docs/manual.txt", "../secreto.txt", "docs/../../secreto.txt", secreto_abs,
                   "docs/../leeme.txt"]:
        print(f"\npide: {nombre!r}")
        try:
            print(f"  A) os.path.join + open:      {abrir_mal(nombre)}")
        except OSError as e:
            print(f"  A) os.path.join + open:      error: {e}")
        print(f"  B) resolve + is_relative_to: {abrir_bien(nombre)}")
        print(f"  C) werkzeug safe_join:       {safe_join(base, nombre)}")
    from importlib.metadata import version
    print(f"\n(werkzeug {version('werkzeug')})")


if __name__ == "__main__":
    que = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if que in ("sql", "todo"):
        demo_sql()
    if que in ("xss", "todo"):
        demo_xss()
    if que in ("ruta", "todo"):
        demo_ruta()
