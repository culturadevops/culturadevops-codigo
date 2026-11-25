# Captura la ventana REAL de la app de notas a PNG, para la escena del vídeo 149.
# La narración dice «míralo tú mismo»: esto es lo que se mira. Mismo código de app.py,
# con notas de ejemplo, y ImageGrab sobre el rectángulo de la ventana.
import sys
import tkinter as tk
from pathlib import Path

from PIL import ImageGrab

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "ventana.png")

v = tk.Tk()
v.title("Notas — sin navegador, sin Electron")
v.geometry("420x380+200+120")
v.configure(bg="#0d1117")

caja = tk.Entry(v, font=("Segoe UI", 12), bg="#151b23", fg="#e6edf3",
                insertbackground="#e6edf3", relief="flat")
caja.pack(fill="x", padx=12, pady=(12, 6), ipady=6)
caja.insert(0, "medir antes de opinar")

fila = tk.Frame(v, bg="#0d1117")
fila.pack(fill="x", padx=12)
tk.Button(fila, text="Agregar", bg="#238636", fg="white",
          relief="flat", padx=14, pady=4).pack(side="left")
tk.Button(fila, text="Borrar", bg="#30363d", fg="#e6edf3",
          relief="flat", padx=14, pady=4).pack(side="left", padx=6)

lista = tk.Listbox(v, font=("Segoe UI", 11), bg="#151b23", fg="#e6edf3",
                   selectbackground="#1f6feb", relief="flat", activestyle="none")
lista.pack(fill="both", expand=True, padx=12, pady=12)
for n in ["comprar café", "grabar el vídeo 149", "9,63 MB y un solo archivo",
          "0 dependencias: tkinter viene con Python", "responder comentarios"]:
    lista.insert(tk.END, n)
lista.selection_set(2)


def capturar():
    v.update_idletasks()
    x, y = v.winfo_rootx(), v.winfo_rooty()
    w, h = v.winfo_width(), v.winfo_height()
    # El marco de la ventana (barra de título) queda fuera del root: se añade a mano.
    marco = 8
    barra = 32
    img = ImageGrab.grab(bbox=(x - marco, y - barra, x + w + marco, y + h + marco))
    img.save(SALIDA)
    print(f"[ok] {SALIDA} · {img.size[0]}x{img.size[1]}")
    v.destroy()


v.after(600, capturar)
v.mainloop()
