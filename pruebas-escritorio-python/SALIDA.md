# SALIDA — Escritorio con Python contra Electron, medidos en esta máquina

> Corrida del 2026-08-30. ⛔ Ninguna cifra de blog: todo salió de aquí. La app es la MISMA
> en los dos lados (notas rápidas: ventana, alta, borrado, persistencia): `python/app.py`
> (tkinter, solo stdlib, ~60 líneas) y `electron/` (main.js + index.html).

- Python 3.11 (del sistema) · tkinter 8.6 · PyInstaller (instalado hoy vía pip)
- Electron 44.0.0 · @electron/packager 20.3.0 · node del sistema
- Windows 11. ⚠️ App Control NO bloqueó los .exe sin firmar de PyInstaller (se temía que sí).
- ⚠️ Gotcha real de esta máquina: `ELECTRON_RUN_AS_NODE=1` heredado del entorno (VS Code)
  hace que Electron arranque como Node pelado y `app` sea undefined. Hay que limpiarla.

## 1 · La app en desarrollo

| | |
|---|---|
| `python app.py` | ventana en **412 ms** · **27,5 MB** WorkingSet (13,3 privada) · 1 proceso |
| dependencias Python | **0** (tkinter viene con Python) |
| `node_modules` de Electron | **392,5 MB** (el `electron.exe` solo: 233,1 MB) |
| Electron corriendo | **4 procesos** · **294,5 MB** WorkingSet total (94.016+92.844+46.332+68.328 KB) |

## 2 · Lo que se distribuye

| variante | tamaño | archivos | build |
|---|---|---|---|
| PyInstaller `--onefile` | **9,63 MB** (10.100.002 B) | **1** | 4,8 s |
| PyInstaller `--onedir` | 23 MB | 937 | ~5 s |
| Electron (`electron-packager`) | **365,8 MB** | 73 | 2,6 s (sin contar los 392 MB de node_modules) |

Ratio del paquete: **38x** (365,8 / 9,63).

## 3 · Arranque hasta ventana (medido con MainWindowHandle)

| | 1ª vez (frío) | 2ª vez (caché) |
|---|---|---|
| `--onefile` (notas.exe) | 707 ms | **689 ms** (el autoextraído no se cachea) |
| `--onedir` | 977 ms | **149 ms** |
| Electron empaquetado | 6.560 ms | **167 ms** |

⚠️ El giro honesto: en arranque caliente **Electron le gana al onefile** (167 contra 689 ms).
El autoextraído del onefile se paga en cada arranque. La solución es `--onedir` (149 ms), al
precio de 937 archivos. El argumento contra Electron NO es la velocidad: es el peso (38x) y
la RAM (294,5 contra 27,5-39 MB).

## 4 · RAM de los empaquetados

| | procesos | WorkingSet |
|---|---|---|
| notas.exe (onefile) | 2 | **39,1 MB** |
| Electron | 4 | **294,5 MB** |

## Lo que NO se midió (y no se afirma con cifra)

- Firmar el .exe (SmartScreen avisará en máquinas ajenas): se dice como criterio, sin número.
- Flet/otras librerías: se mencionan como opción, sin cifras.
