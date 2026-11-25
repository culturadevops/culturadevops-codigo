# 10 intentos por SSH y 167 alertas: solo una hay que mirar — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · dentro de lab-wazuh-victima

```console
$ for i in 1 2 3 4 5 6 7 8 9 10; do
$   echo "malaclave$i" | ssh becario@127.0.0.1 exit
$ done

Permission denied, please try again.
Permission denied, please try again.
...
```

## 2. en mi máquina · las reglas que saltaron

```console
19  Rule: 5760 (level 5) ->
      'sshd: authentication failed.'

 1  Rule: 5763 (level 10) ->
      'sshd: brute force trying to get access to the system'
```
