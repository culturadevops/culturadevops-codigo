# Salida ejecutada — vídeo 229 «Loki, ¿la alternativa a Elasticsearch este 2026?»

> Corrida del 2026-09-09. Loki 3.2.0 y Elasticsearch 8.15.0, cada uno en su contenedor, misma red
> de Docker, **el mismo corpus de 200.000 líneas** (32 MB, semilla fija). Reproducible con
> `bash demo.sh`.

---

## ✅ La comprobación que valida todo lo demás

```
C · ¿TIENEN LOS DOS EL MISMO CORPUS?
   Elasticsearch: 200000 documentos
   Loki:          200000 lineas
   ✅ los dos tienen lo mismo: la comparación vale
```

Esto está lo primero a propósito. **Tres corridas anteriores dieron números preciosos y falsos**
porque a Loki solo le había entrado parte del corpus (ver los tropiezos al final). Sin esta
igualdad, todo lo de abajo sería adorno.

---

## 🥇 LA TABLA

| | Loki | Elasticsearch | |
|---|---|---|---|
| memoria **en reposo** | **35,3 MB** | 1,584 GB | **45× menos** |
| memoria tras ingerir | **114 MB** | 1,76 GB | **15× menos** |
| ingerir 200.000 líneas | **1,9 s** | 3,3 s | 1,7× más rápido |
| los datos en disco | **5,1 MB** | 13,4 MB | **2,6× menos** |
| su directorio entero | 38,7 MB | — | (con registro de escritura) |
| búsqueda por **etiqueta** | 49,1 ms | **2,9 ms** | ES **17× más rápido** |
| búsqueda por **contenido** | 83,9 ms | **3,1 ms** | ES **27× más rápido** |

## 🥇 EL RESULTADO QUE LE DA LA VUELTA AL VÍDEO

Iba a contar que Loki gana en las búsquedas por etiqueta, porque eso es lo único que indexa. **Y
no.** Elasticsearch fue más rápido en **las dos**, incluida la que Loki debería dominar: 2,9 ms
contra 49,1.

Así que la tesis no puede ser «Loki es más rápido». Es esta:

> **Loki no es más rápido. Es más barato.**

45 veces menos memoria en reposo y 2,6 veces menos disco. Elasticsearch gana en latencia porque
para eso indexa todo, y por eso mismo necesita ese giga y medio de memoria antes de haber recibido
un solo registro.

⚠️ Y con honestidad sobre la escala: **200.000 líneas caben en la memoria de cualquiera**. Con ese
tamaño, Elasticsearch responde en milisegundos a todo y su índice le sale gratis. La diferencia
que se mide aquí no es la latencia: es **cuánto hierro necesitas encendido** para tenerlo listo.
Esa cuenta cambia de signo cuando son terabytes y años, y eso no cabe en este banco.

## Detalle: lo que ocupa cada uno, con cuidado

```
   Elasticsearch (indice registros):            13.4mb   200000 docs
   Loki (todo su directorio de datos):          38.7M
   Loki, solo los trozos (los datos de verdad):  5.1M
```

Hay que dar los dos números de Loki o se engaña. Los **datos** ocupan 5,1 MB contra 13,4: ahí está
el 2,6× de la tesis, y sale de no indexar el contenido. Pero su directorio entero son 38,7 MB
porque incluye el registro de escritura anticipada, que a esta escala pesa más que los datos. Con
un corpus de verdad esa proporción se invierte.

## La memoria, que es el número gordo

```
   en reposo, antes de un solo registro:   loki 35.31MiB   ·   elastic 1.584GiB
   después de ingerir 200.000:             loki  114.1MiB  ·   elastic 1.76GiB
```

**Elasticsearch pide un giga y medio antes de que le mandes nada.** Es una máquina virtual de Java
con su montón reservado. Loki arranca con 35 MB. Si tienes que pagar esa máquina encendida todo el
mes, ahí está la factura del vídeo.

---

## ⛔ Lo que se tocó de la configuración, y por qué

Dos cosas en Loki, las dos **barreras de configuración, no propiedades del diseño**. Se dicen para
que nadie piense que hubo trampa:

1. `chunk_idle_period: 5s` y `max_chunk_age: 15s`. Por defecto Loki tiene los trozos en memoria
   hasta media hora; medir el disco antes de que los vuelque daba **kilobytes**.
2. Los límites de ritmo de ingesta, subidos. Con los de serie (4 MB/s) Loki devolvía `429` a mitad
   de la carga.

## Tropiezos reales (van en el guion)

1. 🥇 **Loki rechaza los registros viejos y yo no miraba el código de respuesta.** Mi corpus tenía
   fechas de 2025 y Loki contestaba `400 · timestamp too old ... oldest acceptable timestamp is:`
   a **todos** los envíos. La medición decía que Loki ocupaba 8 KB con 200.000 líneas, y las
   búsquedas daban cero. Por defecto no acepta nada de hace más de una semana.
2. **Elasticsearch daba 0 en la búsqueda por etiqueta** porque una cadena se indexa por defecto
   como texto analizado, y un término exacto no casa con eso. Hay que declarar el campo como
   `keyword` (o buscar en `campo.keyword`).
3. **El límite de ritmo de Loki**, arriba: `429` a mitad de la carga, sin que nada más se quejara.
4. **`track_total_hits`**: Elasticsearch tope los totales en 10.000, así que mi propia
   comprobación de igualdad daba un falso negativo. El motor estaba bien; el que contaba mal era yo.

> Los cuatro tienen el mismo síntoma: **números que salen, parecen razonables, y son mentira**.
> Por eso la comprobación de igualdad del corpus está en el guion y no solo en el código.
