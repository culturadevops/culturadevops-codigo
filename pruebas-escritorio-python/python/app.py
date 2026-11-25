# La app del vídeo: notas rápidas de escritorio. SOLO librería estándar (tkinter + json).
# Pequeña pero de verdad: ventana, lista, alta y borrado, y persiste en un json al lado.
import json
import tkinter as tk
from pathlib import Path

ARCHIVO = Path(__file__).with_name("notas.json")


def cargar():
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except Exception:
        return []


def guardar():
    ARCHIVO.write_text(json.dumps(list(lista.get(0, tk.END)), ensure_ascii=False, indent=1),
                       encoding="utf-8")


def agregar(_=None):
    t = caja.get().strip()
    if t:
        lista.insert(tk.END, t)
        caja.delete(0, tk.END)
        guardar()


def borrar(_=None):
    for i in reversed(lista.curselection()):
        lista.delete(i)
    guardar()


v = tk.Tk()
v.title("Notas — sin navegador, sin Electron")
v.geometry("420x380")
v.configure(bg="#0d1117")

caja = tk.Entry(v, font=("Segoe UI", 12), bg="#151b23", fg="#e6edf3",
                insertbackground="#e6edf3", relief="flat")
caja.pack(fill="x", padx=12, pady=(12, 6), ipady=6)
caja.bind("<Return>", agregar)

fila = tk.Frame(v, bg="#0d1117")
fila.pack(fill="x", padx=12)
tk.Button(fila, text="Agregar", command=agregar, bg="#238636", fg="white",
          relief="flat", padx=14, pady=4).pack(side="left")
tk.Button(fila, text="Borrar", command=borrar, bg="#30363d", fg="#e6edf3",
          relief="flat", padx=14, pady=4).pack(side="left", padx=6)

lista = tk.Listbox(v, font=("Segoe UI", 11), bg="#151b23", fg="#e6edf3",
                   selectbackground="#1f6feb", relief="flat", activestyle="none")
lista.pack(fill="both", expand=True, padx=12, pady=12)
for n in cargar():
    lista.insert(tk.END, n)

v.mainloop()
