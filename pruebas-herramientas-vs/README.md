# pruebas-herramientas-vs

Código de estos vídeos del canal Cultura DevOps:

- [¿Nginx o Caddy? Lo medí: 3,5 veces más peticiones con la mitad de CPU (2026)](https://youtu.be/ZP-5pO0TXEA)
- [¿Traefik o Nginx? Lo medí: Nginx ×2,5, pero de fábrica Traefik no se cae (2026)](https://youtu.be/fd5AmKAL3fQ)
- [¿HAProxy o Nginx? Lo medí: empate por HTTP, HAProxy +59 % con HTTPS (2026)](https://youtu.be/9YtBDLy8nZk)
- [¿Postgres o MySQL? Lo medí: más transacciones con la mitad de memoria (2026)](https://youtu.be/Y6HFE2mX_wo)
- [¿Redis o Valkey? Lo medí: empate en velocidad, y io-threads te puede triplicar la CPU (2026)](https://youtu.be/BncqAU9GEZM)

## Qué es

El código, los scripts de medición y los resultados (`SALIDA*.md`) que se ejecutaron para el vídeo. Las cifras del vídeo salen de estas ejecuciones.

## Cómo ejecutarlo

Lee los archivos de la carpeta: cada script indica en su cabecera cómo se lanza.

Casi todo corre dentro de Docker para que el resultado no dependa de tu máquina. Algunos scripts se escribieron para la estructura de carpetas original (rutas como `<repo>` o `<proyecto>`): ajústalas a la tuya.
