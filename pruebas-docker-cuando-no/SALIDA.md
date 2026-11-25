# SALIDA — Lo que cuesta Docker Desktop por existir (Windows), medido en esta máquina

> Corrida del 2026-08-31. ⛔ Ninguna cifra de blog.

| | |
|---|---|
| WSL/VM apagado (antes de arrancar Docker Desktop) | proceso `vmmem` **inexistente**: 0 MB |
| Docker Desktop arrancado, **0 contenedores** corriendo | `vmmem` = **3.298 MB** |
| (control con los 3 contenedores del lab del canal, ~100 MB reales entre ellos) | `vmmem` = 3.349 MB |

Lectura: en Windows, Docker corre dentro de una máquina virtual (WSL2), y esa VM reserva
**~3,3 GB de RAM en esta máquina solo por existir**, sin servir un solo contenedor. En
Linux nativo ese peaje no existe (criterio, no medido aquí).

## Números de la casa que este vídeo reutiliza (citados con su corrida)

- Arranque de contenedor vs proceso (corrida 2026-08-30, pruebas-python-node): primera
  respuesta del contenedor 190–297 ms; el proceso solo, 1–3 ms.
- Imágenes (corrida 2026-08-30, pruebas-docker-python): la misma API, 1,63 GB con el
  Dockerfile del tutorial · 199 MB con el bueno.
- Contexto de build con BuildKit (misma corrida): 2 bytes con 80 MB de basura al lado.
