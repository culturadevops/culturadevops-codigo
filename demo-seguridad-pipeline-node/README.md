# npm audit y njsscan: seguridad en el pipeline para Node.js (y lo que se les escapa)

Código del vídeo [«npm audit y njsscan: seguridad en el pipeline para Node.js (y lo que se les escapa)»](https://youtu.be/5ZvN-pkMLP0) del canal Cultura DevOps.

## Qué es

El código, los scripts de medición y los resultados (`SALIDA*.md`) que se ejecutaron para el vídeo. Las cifras del vídeo salen de estas ejecuciones.

## Cómo ejecutarlo

```bash
bash correr.sh
```

Casi todo corre dentro de Docker para que el resultado no dependa de tu máquina. Algunos scripts se escribieron para la estructura de carpetas original (rutas como `<repo>` o `<proyecto>`): ajústalas a la tuya.

## Resultados

Los resultados de la ejecución que sale en el vídeo están en los archivos `SALIDA*.md`.

## Nota sobre la clave de ejemplo

En el vídeo la aplicación lleva una clave de Stripe **falsa** con formato `sk_live_...` para que los escáneres la detecten. Aquí se cambió por `CLAVE_STRIPE_FALSA_DE_EJEMPLO` porque GitHub bloquea cualquier cadena con ese formato. Para reproducir el hallazgo, pon cualquier valor con formato `sk_live_` seguido de 24 caracteres.
