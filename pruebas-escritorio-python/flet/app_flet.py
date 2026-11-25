# La MISMA app de notas del vídeo 149, tercera versión: Flet (Flutter para Python).
# Mismo contrato: escribir, agregar, borrar, persistir en un json al lado.
import json
from pathlib import Path

import flet as ft

ARCHIVO = Path(__file__).with_name("notas.json")


def cargar():
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except Exception:
        return []


def main(page: ft.Page):
    page.title = "Notas — Flet"
    page.window.width = 420
    page.window.height = 380
    page.bgcolor = "#0d1117"
    page.padding = 12

    lista = ft.ListView(expand=True, spacing=4)

    def guardar():
        ARCHIVO.write_text(json.dumps([c.title.value for c in lista.controls],
                                      ensure_ascii=False, indent=1), encoding="utf-8")

    def fila(texto):
        return ft.ListTile(title=ft.Text(texto, color="#e6edf3", size=14), dense=True)

    def agregar(_):
        if caja.value.strip():
            lista.controls.append(fila(caja.value.strip()))
            caja.value = ""
            guardar()
            page.update()

    def borrar(_):
        if lista.controls:
            lista.controls.pop()
            guardar()
            page.update()

    caja = ft.TextField(hint_text="una nota…", bgcolor="#151b23", color="#e6edf3",
                        border_color="#30363d", on_submit=agregar)
    page.add(
        caja,
        ft.Row([ft.FilledButton("Agregar", on_click=agregar,
                                style=ft.ButtonStyle(bgcolor="#238636", color="white")),
                ft.OutlinedButton("Borrar", on_click=borrar)]),
        lista,
    )
    for n in cargar():
        lista.controls.append(fila(n))
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
