# El 94% del disco de Wazuh no es tuyo: lo que cuesta de verdad — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · docker stats, en reposo

```console
indexer      1,671 GiB   10,88 %
manager      759,2 MiB    4,83 %
dashboard    225,3 MiB    1,43 %
victima       95,0 MiB    0,60 %
```

## 2. en mi máquina · docker images

```console
wazuh-indexer:4.9.2      4,23 GB
wazuh-manager:4.9.2      2,00 GB
wazuh-dashboard:4.9.2    1,79 GB
certs-generator          218 MB
```

## 3. en mi máquina · lo que ha crecido cada contenedor

```console
dashboard     77,8 kB
indexer         893 kB
victima         247 MB

manager        10,8 GB
```

## 4. en mi máquina · du dentro del manager

```console
$ du -sh /var/ossec/* | sort -rh | head

11G   /var/ossec/queue
601M  /var/ossec/framework
16M   /var/ossec/ruleset
16M   /var/ossec/logs
```

## 5. en mi máquina · dentro de queue

```console
$ du -sh /var/ossec/queue/* | sort -rh | head

5,6G   queue/vd
4,6G   queue/vd_updater
8,2M   queue/indexer
3,0M   queue/db
```

## 6. en mi máquina · los volúmenes, tras varios días

```console
manager-logs      15,64 MB
indexer-data      13,29 MB
manager-config     2,76 MB
```
