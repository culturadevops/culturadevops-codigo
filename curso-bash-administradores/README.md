# 🐚 Bash para administradores — material del curso

Código del vídeo [«Curso de Bash para administradores: el lenguaje, no los comandos»](https://youtu.be/HHVm7J6JP38) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/HHVm7J6JP38**

---

> 🎬 Acompaña al vídeo **«Curso de Bash para administradores: el lenguaje, no los comandos»** del canal **Cultura DevOps** (solo miembros).

Código del curso **«Bash para administradores: el lenguaje, no los comandos»** de
[Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros del canal.

> **Esto no es un curso de find, grep y tuberías** (eso está en el curso de Linux del canal).
> Esto es Bash como *lenguaje*: comillas, expansiones, códigos de salida, arrays, trap. Que es
> justo donde están los fallos que borran carpetas y dejan pipelines en verde.

Cada lección reproduce el fallo en tu máquina y luego enseña cómo se escribe para que no pase.

## Cómo usar esto

```bash
git clone <este-repo> && cd curso-bash-administradores
bash --version            # hace falta bash 4+ (por los arrays asociativos)
python ejecutar_todo.py   # corre las 12 lecciones y regenera SALIDA.md
```

Solo hace falta bash y las herramientas de siempre (tar, grep, xargs). Todo se escribe en
carpetas temporales que se borran al terminar.

> ⚠️ **Lo que nunca vas a encontrar aquí:** un comando destructivo con una ruta absoluta que se
> ejecute de verdad. El `rm -rf "$DIR"/*` con la variable vacía **se imprime**; el destrozo que
> sí ocurre es relativo y dentro de un `mktemp -d`. Escribir la otra versión «para probar» es
> exactamente como se pierden máquinas.

## Las 12 lecciones

| # | directorio | la trampa | lo que hay que hacer |
|---:|---|---|---|
| 1 | `01_comillas` | `rm $ARCHIVO` con un espacio borra dos archivos que no eran | entrecomillar siempre; `[[ ]]` es la excepción |
| 2 | `02_modo_estricto` | sin `set -e` el script sigue tras el fallo y sale con 0 | `set -euo pipefail`, y saber dónde NO salta |
| 3 | `03_rm_rf` | `rm -rf "$DIR"/*` con `$DIR` vacío es `rm -rf /*` | `${DIR:?}`, lista negra de rutas, `cd` y borrar desde dentro |
| 4 | `04_codigos` | el código de una tubería es el del último; `local x=$(...)` se lo come | `PIPESTATUS`, `pipefail`, declarar y asignar aparte |
| 5 | `05_comparar` | `[ $VACIA = x ]` ni compara; `>` ordena texto, no números | `[[ ]]`, `-gt/-lt`, `(( ))`, `${VAR:-}` y `${VAR:?}` |
| 6 | `06_leer` | `for l in $(cat f)` da 16 vueltas para 5 líneas | `while IFS= read -r`, y ojo con el subshell de la tubería |
| 7 | `07_arrays` | una lista de opciones en un texto pierde los espacios | arrays y `"${ARR[@]}"`; construir el comando sin `eval` |
| 8 | `08_expansion` | `*.log` sin coincidencias se queda tal cual; `"~/copias"` no es tu home | `nullglob`, `$HOME`, `${VAR##*/}` y compañía |
| 9 | `09_trap` | el temporal y el cerrojo se quedan si el script muere | `trap limpiar EXIT` + `INT TERM`, y `mktemp` |
| 10 | `10_paralelo` | `&` sin `wait`: el script dice OK y los hijos siguen | `wait $pid` por proceso, `xargs -P N`, salida a archivos |
| 11 | `11_portable` | `#!/bin/sh` con bashismos: falla solo en el contenedor | shebang correcto y `shellcheck` |
| 12 | `12_proyecto` | — | `respaldo.sh`: estricto, con cerrojo, trap, verificación y rotación |

`12_proyecto/respaldo.sh` es un script de verdad, con `--dry-run` y códigos de salida
(0 hecho · 1 fallo · 2 mal llamado · 75 hay otra copia en curso). Úsalo de base para el tuyo.

## La regla de la casa

Todo lo que se ve en el vídeo está **ejecutado**, no copiado. `SALIDA.md` es la salida literal
de `ejecutar_todo.py` en la máquina donde se grabó. Está grabado sobre Git Bash en Windows: por
eso los permisos de `mktemp -d` salen 755 y no 700, y por eso `/bin/sh` es bash. Las dos cosas
se dicen en su lección: son parte de lo que enseña.

## Licencia

El código es para que lo copies, lo rompas y lo uses en tu trabajo. Los vídeos son del canal.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Bash 4 o superior (Linux, macOS o Git Bash en Windows).
- Python 3.10 o superior (para `ejecutar_todo.py`; solo biblioteca estándar salvo que se diga)

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-bash-administradores
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-bash-administradores/
├── 01_comillas/
│   └── comillas.sh
├── 02_modo_estricto/
│   └── modo_estricto.sh
├── 03_rm_rf/
│   └── variable_vacia.sh
├── 04_codigos/
│   └── codigos_y_tuberias.sh
├── 05_comparar/
│   └── comparar.sh
├── 06_leer/
│   └── leer_lineas.sh
├── 07_arrays/
│   └── arrays.sh
├── 08_expansion/
│   └── expansion.sh
├── 09_trap/
│   └── trap_y_limpieza.sh
├── 10_paralelo/
│   └── en_paralelo.sh
├── 11_portable/
│   └── portable.sh
├── 12_proyecto/
│   ├── escenario.sh
│   └── respaldo.sh
├── .gitignore
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
