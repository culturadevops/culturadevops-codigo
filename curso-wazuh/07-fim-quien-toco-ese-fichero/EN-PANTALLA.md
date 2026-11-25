# Toqué el fichero y esperé 5 minutos: nada. FIM en Wazuh, de verdad — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · lo que vigila de fábrica

```console
<directories>/etc,/usr/bin,/usr/sbin</directories>
<directories>/bin,/sbin,/boot</directories>
```

## 2. en mi máquina · la frecuencia, de fábrica

```console
<frequency>43200</frequency>

43.200 segundos = 12 horas
```

## 3. en mi máquina · el antes

```console
$ ls -l /etc/hosts; md5sum /etc/hosts

-rw-r--r-- 1 root root 167 /etc/hosts
4a56fb9f29e101e24923b6f220d5a8e4
```

## 4. en mi máquina · el después

```console
$ echo "10.0.0.99 impostor.local" >> /etc/hosts
$ ls -l /etc/hosts; md5sum /etc/hosts

-rw-r--r-- 1 root root 218 /etc/hosts
18eb6c4494197450847b9992a6f684c4
```

## 5. en mi máquina · lo que llegó al servidor

```console
Rule: 550 (level 7) ->
  'Integrity checksum changed.'

Rule: 510 (level 7) ->
  'Host-based anomaly detection event'
```
