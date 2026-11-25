# Los 4 tipos de métrica de Prometheus y cuál toca en cada caso — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. un contador de verdad

```console
prometheus_http_requests_total
  tipo:  counter
  ayuda: Counter of HTTP requests.
```

## 2. un contador que baja

```console
antes de reiniciar la tienda:   70
despues de reiniciarla:          5

# el contador ha BAJADO
```

## 3. un medidor de verdad

```console
process_resident_memory_bytes
  tipo:  gauge
  ayuda: Resident memory size in bytes.
```

## 4. un histograma de verdad

```console
prometheus_http_request_duration_seconds
  tipo:  histogram
  ayuda: Histogram of latencies for
```

## 5. un resumen de verdad

```console
go_gc_duration_seconds
  tipo:  summary
  ayuda: A summary of the wall-time
```
