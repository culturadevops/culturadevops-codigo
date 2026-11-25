# El escaneo de configuración tardó 0 segundos (y el panel se quedó en verde) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · ejemplos de las comprobaciones

```console
Ensure /tmp is a separate partition.
Ensure nodev option set on /tmp partition.
Ensure noexec option set on /tmp partition.
Ensure nosuid option set on /tmp partition.
Ensure separate partition exists for /var.
```

## 2. en mi máquina · el log del agente

```console
sca: INFO: Module started.
sca: INFO: Loaded policy 'cis_ubuntu22-04.yml'
sca: INFO: Starting Security Configuration
           Assessment scan.
sca: INFO: Skipping policy: 'Check Ubuntu version.'
scan finished. Duration: 0 seconds.
```

## 3. en mi máquina · el nivel de cada línea

```console
INFO: Module started.
INFO: Loaded policy ...
INFO: Starting ... scan.
INFO: Skipping policy ...
INFO: scan finished. Duration: 0 seconds.
```
