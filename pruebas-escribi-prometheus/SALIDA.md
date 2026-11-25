# Salida ejecutada — vídeo 221 «Escribí un Prometheus en Python y Grafana se conectó sin notarlo»

> Corrida del 2026-09-08. Tres contenedores en la misma red de Docker:
> `app` (python:3.12-alpine, el servicio medido), `prometeillo` (python:3.12-alpine, nuestro
> Prometheus de 200 líneas sin dependencias) y **`grafana/grafana:latest`, la imagen oficial, sin
> parches ni adaptadores**. Reproducible con `bash demo.sh`.

---

## 1 · El formato de exposición es TEXTO

```
# HELP peticiones_total Peticiones atendidas desde el arranque.
# TYPE peticiones_total counter
peticiones_total{ruta="/",codigo="200"} 65
peticiones_total{ruta="/",codigo="500"} 4
peticiones_total{ruta="/api/libros",codigo="200"} 71
peticiones_total{ruta="/api/libros",codigo="500"} 6
peticiones_total{ruta="/login",codigo="200"} 80
peticiones_total{ruta="/login",codigo="500"} 2
peticiones_total{ruta="/salud",codigo="200"} 65
peticiones_total{ruta="/salud",codigo="500"} 7
```

Eso es todo. Una línea por serie: `nombre{etiquetas} valor`. Se lee con un `curl`, y esto vale
igual contra el Prometheus de tu empresa.

## 2 · Grafana oficial arrancó

```json
{ "database": "ok", "version": "13.2.1", "commit": "56cd3e9288d8255fecebe5d05b48d191f50674b5" }
```

## 3 · 🥇 EL BOTÓN DE «Guardar y probar», CONTESTADO POR 200 LÍNEAS DE PYTHON

```json
{"details":{"application":"Prometheus","features":{"rulerApiEnabled":false}},
 "message":"Successfully queried the Prometheus API.","status":"OK"}
```

**Grafana 13.2.1 dice, con sus propias palabras, que consultó correctamente la API de Prometheus.**
Detrás no hay Prometheus: hay `prometeillo.py`.

## 4 · 🥇 Y UN PANEL PIDIENDO DATOS DE VERDAD

Lo que manda un panel de serie temporal al cargarse, por `/api/ds/query` de Grafana:

```
   Grafana devolvio 8 series al panel
     /            codigo=200  4 puntos  ultimo=428
     /            codigo=500  4 puntos  ultimo=20
     /api/libros  codigo=200  4 puntos  ultimo=397
     /api/libros  codigo=500  4 puntos  ultimo=26
```

No es una captura de pantalla: es Grafana devolviendo las series ya convertidas a sus estructuras
de datos internas, listas para pintar. Lo único que se cambió fue la URL del origen de datos.

## 5 · 🥇 LA CARDINALIDAD, MEDIDA

Misma métrica, misma aplicación. Lo único que cambia es que se añade `usuario="uN"` a las
etiquetas:

```
   series sin la etiqueta de usuario:   8
   series con la etiqueta de usuario:   1853      (en 20 segundos)
```

De 8 a 1.853 en veinte segundos, y subiendo para siempre. Cada combinación distinta de etiquetas
es una **serie nueva**, con su propia lista de puntos en el tiempo. Esa es la factura que llega a
fin de mes y el motivo por el que meter un identificador de usuario, o una URL con el id dentro,
en una etiqueta es el error caro de verdad.

## 6 · 🥇 POR QUÉ UN PROCESO CORTO NO APARECE NUNCA

Un trabajo que vive 3 segundos, exponiendo su métrica los 3 segundos, con el scrape cada 2:

```
   puntos guardados de trabajito_hecho: 0
```

**Cero.** No es que llegara tarde: es que nadie fue nunca a buscarlo a ese host, porque el que
recoge solo conoce la lista de objetivos que le diste. Esto explica de golpe la pregunta que hace
todo el mundo el primer mes, y es también el motivo de que exista el `pushgateway`.

## 7 · La métrica que nadie expone y siempre está

```
   up {'instance': 'app:9101', 'job': 'demo'} = 1.0
```

`up` no la escribe el medido: la escribe el que recoge, uno por objetivo, 1 si contestó y 0 si no.
Por eso puedes alertar de que algo se cayó, aunque esté tan caído que no pueda decírtelo.

---

## ⛔ Lo que NO es, y se dice en el vídeo con estas palabras

- No hay PromQL de verdad: solo se resuelve `nombre{etiqueta="valor"}`. Nada de `rate()`, ni
  operadores, ni agregaciones.
- No hay almacenamiento en disco. Todo vive en memoria y se pierde al reiniciar.
- No hay reglas, ni alertas, ni federación, ni descubrimiento de servicios.
- Sirve para entender el modelo y para pruebas. No para producción.
