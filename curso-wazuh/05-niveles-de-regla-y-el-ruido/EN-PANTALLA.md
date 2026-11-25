# 1.313 alertas sin que pasara nada: los niveles de Wazuh y el ruido — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · índices del laboratorio

```console
index                          docs   tamaño
wazuh-alerts-4.x-2026.08.23    5265    9.5mb
wazuh-monitoring-2026.34w         4   32.7kb
wazuh-statistics-2026.34w         2   24.1kb
```

## 2. en mi máquina · reglas de las que no avisan de nada

```console
Rule 502 (nivel 3)   Wazuh server started
Rule 503 (nivel 3)   Wazuh agent started
Rule 506 (nivel 3)   Wazuh agent stopped
```

## 3. en mi máquina · los mismos sucesos, con su nivel

```console
Rule 510  (7)  anomalía en el sistema de ficheros
Rule 550  (7)  Integrity checksum changed
Rule 5760 (5)  sshd: authentication failed
Rule 5763 (10) sshd: brute force trying to get access
```

## 4. en mi máquina · esa ventana, por nivel

```console
19  (level 5)
 7  (level 7)
 4  (level 3)
 1  (level 10)   <- esta
```
