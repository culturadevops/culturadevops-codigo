# demo-sast-por-lenguaje

Código de estos vídeos del canal Cultura DevOps:

- [DevSecOps pipeline: un escáner de seguridad para cada lenguaje (PHP, Python, Go, Java, Node)](https://youtu.be/fcBfWr6VleU)
- [Semgrep vs CodeQL vs SonarQube: el mismo código vulnerable en 5 lenguajes (medido)](https://youtu.be/4f6qZc9PoEA)

## Qué es

El código, los scripts de medición y los resultados (`SALIDA*.md`) que se ejecutaron para el vídeo. Las cifras del vídeo salen de estas ejecuciones.

Más detalle en [LEEME.md](LEEME.md).

## Cómo ejecutarlo

```bash
python correr.py
```

Casi todo corre dentro de Docker para que el resultado no dependa de tu máquina. Algunos scripts se escribieron para la estructura de carpetas original (rutas como `<repo>` o `<proyecto>`): ajústalas a la tuya.

## Resultados

Los resultados de la ejecución que sale en el vídeo están en los archivos `SALIDA*.md`.
