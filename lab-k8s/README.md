# lab-k8s

Código de estos vídeos del canal Cultura DevOps:

- [Argo CD: hice push y tardó 189 segundos (prune y selfHeal, medidos)](https://youtu.be/0mNinBCkUiI)
- [Renovate: 13 actualizaciones y abrió 2 (el límite por hora y cómo agrupar)](https://youtu.be/AaxftRj2izI)

## Qué es

El código, los scripts de medición y los resultados (`SALIDA*.md`) que se ejecutaron para el vídeo. Las cifras del vídeo salen de estas ejecuciones.

## Cómo ejecutarlo

```bash
python lab.py
```

Casi todo corre dentro de Docker para que el resultado no dependa de tu máquina. Algunos scripts se escribieron para la estructura de carpetas original (rutas como `<repo>` o `<proyecto>`): ajústalas a la tuya.
