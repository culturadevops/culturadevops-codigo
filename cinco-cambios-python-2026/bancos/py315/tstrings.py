# 715 · t-strings (PEP 750, Python 3.14): la plantilla llega como objeto y TÚ decides cómo se escapa cada valor.
# ⛔ Nada se ejecuta en un shell: solo se imprime el comando que se armaría.
import shlex
from string.templatelib import Interpolation

archivo = "informe.txt; rm -rf /tmp/x"

f = f"cat {archivo}"
print("f-string :", f)

t = t"cat {archivo}"
print("tipo     :", type(t).__name__)
print("strings  :", t.strings)
print("valores  :", t.values)


def shell(plantilla):
    return "".join(shlex.quote(str(p.value)) if isinstance(p, Interpolation) else p for p in plantilla)


print("t-string :", shell(t))
