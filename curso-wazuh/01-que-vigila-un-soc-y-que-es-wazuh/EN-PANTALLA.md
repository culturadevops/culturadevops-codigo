# Wazuh: 752 alertas antes de que entrara nadie (y qué es un SOC de verdad) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo que pesa cada pieza

```console
$ docker stats --no-stream

lab-wazuh-indexer     1.5GiB
lab-wazuh-manager   538.5MiB
lab-wazuh-dashboard 182.3MiB
```

## 2. lo que vio Wazuh

```console
regla 5710  nivel  5  x19   usuario inexistente
regla 5503  nivel  5  x9    login fallido
regla 5551  nivel 10  x1    multiples fallos
regla 5712  nivel 10  x1    BRUTE FORCE
```
