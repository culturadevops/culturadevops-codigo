# 🌙 Python para la guardia — material del curso

Código del vídeo [«Python para la guardia: leer logs a las 3 de la mañana»](https://youtu.be/sL2lyEOFFSI) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/sL2lyEOFFSI**

---

> 🎬 Acompaña al vídeo **«Python para la guardia: leer logs a las 3 de la mañana»** del canal **Cultura DevOps** (solo miembros).

Código del curso **«Python para la guardia: leer logs y datos operativos»** de
[Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros del canal.

> **Son las 3 de la mañana, suena el teléfono y tienes un log de 2 GB.** No necesitas saber
> ciencia de datos: necesitas leer mucho texto sin tumbar la máquina, contar bien, y no
> engañarte con la media. Cada lección es una de las formas de engañarte, reproducida.

Todas las lecciones trabajan sobre el **mismo incidente**: a las 03:12 UTC la base de datos
agota su pool de conexiones, y durante cuatro minutos falla el 69% de las peticiones. El log lo
genera `comun/registro.py` con la semilla fija, así que en tu máquina sale exactamente igual.

## Cómo usar esto

```bash
git clone <este-repo> && cd curso-python-guardia
python --version          # hace falta 3.10 o superior (zoneinfo)
python ejecutar_todo.py   # corre las 12 lecciones y regenera SALIDA.md
```

**Cero dependencias**: solo biblioteca estándar. Nada de pandas, nada que instalar a las 3 de
la mañana en una máquina que no es la tuya.

## Las 12 lecciones

| # | directorio | la trampa | lo que hay que hacer |
|---:|---|---|---|
| 1 | `01_memoria` | `read()` y `readlines()` se traen el log entero a memoria | el fichero YA es un iterador de líneas; generadores encadenados |
| 2 | `02_parsear` | `split()` por posiciones cuenta trozos de traceback como niveles | regex con grupos con nombre, y **contar lo que no casa** |
| 3 | `03_tiempo` | fechas ingenuas, texto que se ordena mal, el cambio de hora | todo en UTC, `strptime` con `%z`, `zoneinfo` solo para el parte |
| 4 | `04_contar` | 3.083 mensajes «distintos» porque llevan el id dentro | normalizar a un patrón y contar patrones: son 5 |
| 5 | `05_ventanas` | la media de la hora: 51 errores/min, parece ruido | por minuto: 777 en el pico, y el **porcentaje**, no el número |
| 6 | `06_correlacionar` | juntar dos logs por hora: 0% de parejas correctas | índice por identificador de petición |
| 7 | `07_percentiles` | la media dice 183 ms mientras el p99 son 1.650 | p50/p95/p99, y no promediar percentiles nunca |
| 8 | `08_json` | una línea cortada mata el script, o el `except` se la traga | saltar, **contar** las rotas y guardar una muestra |
| 9 | `09_rotados` | `app.log.10` ordena antes que `app.log.2` | ordenar por número de rotación; `gzip.open` en modo texto |
| 10 | `10_final` | leer 18 MB para ver las últimas 20 líneas | `seek` desde el final; y `break` al salir de la ventana |
| 11 | `11_muestreo` | `head -1000` dice 0% de errores en la noche del incidente | muestra repartida (`[::50]`), o contar entero: son milisegundos |
| 12 | `12_proyecto` | — | `triaje.py`: ventana, patrones, percentiles y código de salida |

`12_proyecto/triaje.py` está pensado para copiarlo a la máquina de guardia:

```bash
python triaje.py /var/log/app.log* --desde 03:10 --hasta 03:20
python triaje.py app.log --json     # para pegarlo en el ticket
```

## La regla de la casa

Todo lo que se ve en el vídeo está **ejecutado**, no copiado. `SALIDA.md` es la salida literal
de `ejecutar_todo.py` en la máquina donde se grabó. Los tiempos cambian entre máquinas; los
conteos y los porcentajes, no: el log es el mismo siempre.

## Licencia

El código es para que lo copies, lo rompas y lo uses en tu trabajo. Los vídeos son del canal.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Python 3.10 o superior. Cero dependencias.

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-python-guardia
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-python-guardia/
├── 01_memoria/
│   └── leer_sin_cargar.py
├── 02_parsear/
│   └── partir_la_linea.py
├── 03_tiempo/
│   └── horas_y_zonas.py
├── 04_contar/
│   └── agrupar_mensajes.py
├── 05_ventanas/
│   └── la_media_miente.py
├── 06_correlacionar/
│   └── dos_fuentes.py
├── 07_percentiles/
│   └── la_media_no_sirve.py
├── 08_json/
│   └── logs_json.py
├── 09_rotados/
│   └── ficheros_rotados.py
├── 10_final/
│   └── solo_el_final.py
├── 11_muestreo/
│   └── no_te_mientas.py
├── 12_proyecto/
│   ├── escenario.py
│   └── triaje.py
├── comun/
│   ├── __init__.py
│   └── registro.py
├── .gitignore
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
