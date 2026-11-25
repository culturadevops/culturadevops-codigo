# pruebas-crowdsec-vs-fail2ban

Código de estos vídeos del canal Cultura DevOps:

- [CrowdSec vs Fail2ban: los mismos fallos de SSH, ¿quién bloquea antes? (medido)](https://youtu.be/fc3asOmQoLM)
- [De DevOps a seguridad: la ruta blue team, con 3 laboratorios de defensa en casa](https://youtu.be/3d1bIlFQM_M)

## Qué es

El código, los scripts de medición y los resultados (`SALIDA*.md`) que se ejecutaron para el vídeo. Las cifras del vídeo salen de estas ejecuciones.

## Cómo ejecutarlo

```bash
python correr.py
```

Casi todo corre dentro de Docker para que el resultado no dependa de tu máquina. Algunos scripts se escribieron para la estructura de carpetas original (rutas como `<repo>` o `<proyecto>`): ajústalas a la tuya.

## Resultados

Los resultados de la ejecución que sale en el vídeo están en los archivos `SALIDA*.md`.
