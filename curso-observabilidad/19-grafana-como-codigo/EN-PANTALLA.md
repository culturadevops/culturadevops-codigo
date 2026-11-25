# Grafana como código: borro el contenedor y vuelve con todo — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. las fuentes de datos, en un archivo

```console
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
```

## 2. el tablero, en un archivo

```console
"title": "Tienda · del compose",
"panels": [
  "Peticiones por segundo",
  "Porcentaje de fallo",
  "Latencia media" ]
```

## 3. borrando el contenedor

```console
$ docker rm -f obs-grafana

obs-grafana

# el contenedor ya no existe
```

## 4. y lo levanto de nuevo

```console
$ docker compose up -d grafana

tableros: ['Tienda · del compose']
fuentes:  ['Loki', 'Prometheus']
```
