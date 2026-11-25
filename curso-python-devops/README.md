# 🐍 Python para DevOps — material del curso

Código del vídeo [«Curso de Python básico para administradores de sistemas»](https://youtu.be/Qmh6-9fF_KE) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/Qmh6-9fF_KE**

---

> 🎬 Acompaña al vídeo **«Curso de Python básico para administradores de sistemas»** del canal **Cultura DevOps** (solo miembros).

Código de las lecciones del curso **«Python para DevOps desde cero»** de
[Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros del canal.

> **Esto no es un curso de Python para hacer webs.** Es Python para quien administra máquinas,
> escribe automatizaciones y tiene que leer un `.json` a las tres de la mañana. Cada lección
> parte de una tarea que ya haces —recorrer un log, llamar a un comando, validar un fichero de
> configuración— y enseña la pieza del lenguaje que esa tarea necesita.

## Cómo usar esto

```bash
git clone <este-repo> && cd curso-python-devops
python --version          # hace falta 3.10 o superior
python ejecutar_todo.py   # corre las 12 lecciones y regenera SALIDA.md
```

**Cero dependencias.** Todo funciona con la biblioteca estándar. No hay que instalar nada, no
hay `requirements.txt` que se pudra y dentro de tres años esto seguirá ejecutándose.

Cada lección es un directorio con un script que **se ejecuta solo** y explica lo que hace por
la salida. No hay que leerlos en orden, pero están puestos en el orden del curso.

## Las 12 lecciones

| # | directorio | la pieza del lenguaje | la trampa que enseña |
|---:|---|---|---|
| 1 | `01_entorno` | intérprete, `sys`, entornos virtuales | el `python` que se ejecuta no siempre es el que crees |
| 2 | `02_tipos` | tipos, mutable contra inmutable | dos nombres apuntando a la MISMA lista |
| 3 | `03_cadenas` | cadenas, f-strings, `str` contra `bytes` | concatenar rutas a mano y el `UnicodeDecodeError` |
| 4 | `04_colecciones` | listas, diccionarios, conjuntos, tuplas | buscar en una lista cuando querías un diccionario |
| 5 | `05_flujo` | condicionales, bucles, comprensiones | modificar una lista mientras la recorres |
| 6 | `06_funciones` | argumentos, valores por defecto, `*args` | el argumento mutable por omisión |
| 7 | `07_ficheros` | `pathlib`, leer y escribir, codificación | el `encoding` que te rompe solo en Windows |
| 8 | `08_errores` | `try`/`except`/`finally`, excepciones propias | el `except:` pelado que se traga el Ctrl+C |
| 9 | `09_modulos` | módulos, paquetes, `__name__` | el fichero que se ejecuta al importarlo |
| 10 | `10_stdlib` | `os`, `subprocess`, `json`, `datetime`, `logging` | `shell=True` y el código de salida que nadie mira |
| 11 | `11_clases` | clases, `dataclass` | la clase que debería haber sido un diccionario |
| 12 | `12_proyecto` | todo junto: `argparse` + `logging` + errores | un script que se porta bien en una tubería |

## La regla de la casa

Todo lo que se ve en los vídeos está **ejecutado**, no copiado. `SALIDA.md` es la salida literal
de `ejecutar_todo.py` en la máquina donde se grabó, con su versión de Python y su fecha. Si algo
no coincide en la tuya, es un dato, no un fallo: dilo en los comentarios.

## Licencia

El código es para que lo copies, lo rompas y lo uses en tu trabajo. Los vídeos son del canal.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Python 3.10 o superior. Cero dependencias.

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-python-devops
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-python-devops/
├── 01_entorno/
│   └── comprobar_entorno.py
├── 02_tipos/
│   └── mutable_vs_inmutable.py
├── 03_cadenas/
│   └── formatear_y_bytes.py
├── 04_colecciones/
│   └── elegir_coleccion.py
├── 05_flujo/
│   └── recorrer_sin_romper.py
├── 06_funciones/
│   └── argumento_mutable.py
├── 07_ficheros/
│   └── rutas_y_encoding.py
├── 08_errores/
│   └── excepciones.py
├── 09_modulos/
│   ├── inventario.py
│   └── usar_modulo.py
├── 10_stdlib/
│   └── la_caja_de_herramientas.py
├── 11_clases/
│   └── cuando_una_clase.py
├── 12_proyecto/
│   └── revisar_servicios.py
├── .gitignore
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
