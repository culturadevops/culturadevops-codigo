# SALIDA — Flet, medido en esta máquina (la revancha del vídeo 149)

> Corrida del 2026-08-31. ⛔ Ninguna cifra de blog. La MISMA app de notas del 149, tercera
> versión: `flet/app_flet.py`. Referencias congeladas del 149: tkinter 9,63 MB onefile /
> 27,5 MB RAM / 412 ms · Electron 365,8 MB / 294,5 MB / 167 ms (2ª vez).

## Dependencias (lo que trae `pip install flet`)

| | |
|---|---|
| paquetes `flet*` en site-packages | 4,1 MB |
| cliente Flutter en `~/.flet` (lo baja el PRIMER arranque) | **97 MB** |
| primer arranque (incluye esa descarga/extracción) | **10.141 ms** |
| segundo arranque (`python app_flet.py`) | **940 ms** |

## Corriendo (la app de notas abierta)

| | |
|---|---|
| procesos | **3** (python + cliente Flutter) |
| RAM total | **191,4 MB** |

Comparativa corriendo: tkinter 27,5 · **Flet 191,4** · Electron 294,5 MB.

## Empaquetado

| | |
|---|---|
| `flet pack` (PyInstaller onefile por dentro) | 27,3 s de build |
| `notas-flet.exe` | **70,03 MB**, un archivo |
| ¿corre en esta máquina? | ⛔ **NO: App Control lo bloqueó** («Una directiva de Control de aplicaciones bloqueó este archivo») |
| control del mismo día: el `notas.exe` de tkinter (149) | ✅ corre, ventana en 821 ms |

⚠️ No se afirma la causa del bloqueo (no se verificó qué regla saltó); se afirma el hecho:
mismo día, misma máquina, un exe de PyInstaller corre y el de Flet no. Para distribuir en
Windows con políticas de empresa, esto existe y hay que contarlo.

## La ventana real

`assets/ventana-flet.png` (copiada a `public/om-projects/flet-escritorio/`): interfaz
moderna de verdad (Material), la misma app con sus notas. Captura de la app corriendo.
