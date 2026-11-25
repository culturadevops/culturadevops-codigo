# SALIDA — «System design: hashing consistente» (cultura-devops, vídeo 354)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 14:11:09Z` · `go version go1.27.2 linux/amd64`
- hash: FNV-1a de 64 bits + el mezclador de splitmix64. Los tiempos son de esta máquina.

```
== 1 · De 4 a 5 servidores: ¿qué parte de las 100.000 claves cambia de servidor? ==
  módulo                       79.9 %
  anillo,   1 nodos virtuales   5.8 %
  anillo, 100 nodos virtuales  19.6 %
  rendezvous                   20.2 %   (lo justo: 1 de cada 5 = 20 %)

== 2 · Se cae cache-2 (de 4 a 3) ==
  módulo                       75.0 %
  anillo, 100 nodos virtuales  25.6 %   (lo justo: las de cache-2, 1 de cada 4 = 25 %)
  sus claves se reparten entre: cache-0 5668 · cache-1 9799 · cache-3 10112
  sin nodos virtuales, van a:   cache-0 0 · cache-1 29056 · cache-3 0

== 3 · ¿Cómo de justo es el reparto? 100.000 claves entre 4 servidores ==
  módulo                       el que menos  24733 · el que más  25160 · el más cargado lleva 1.01 veces lo justo
  anillo,    1 nodos virtuales el que menos   6229 · el que más  47722 · el más cargado lleva 1.91 veces lo justo
  anillo,   10 nodos virtuales el que menos  17738 · el que más  29470 · el más cargado lleva 1.18 veces lo justo
  anillo,  100 nodos virtuales el que menos  21225 · el que más  29768 · el más cargado lleva 1.19 veces lo justo
  anillo, 1000 nodos virtuales el que menos  24626 · el que más  25368 · el más cargado lleva 1.01 veces lo justo
  rendezvous                   el que menos  24924 · el que más  25126 · el más cargado lleva 1.01 veces lo justo

== 4 · Lo que cuesta buscar una clave (100.000 búsquedas) ==
   4 servidores · módulo                     46 ns por clave
   4 servidores · anillo (100 virtuales)     63 ns por clave
   4 servidores · rendezvous                131 ns por clave
  50 servidores · módulo                     11 ns por clave
  50 servidores · anillo (100 virtuales)     93 ns por clave
  50 servidores · rendezvous               1389 ns por clave

== 5 · Jump consistent hash: sin anillo y sin memoria ==
  de 4 a 5 servidores:           20.1 %
  reparto entre 4:              el que menos  24689 · el que más  25223 · el más cargado lleva 1.01 veces lo justo
  buscar, 50 servidores:            42 ns por clave

== 6 · Un servidor el doble de grande: el doble de nodos virtuales ==
  cache-0 con 200 nodos, el resto con 100: cache-0 44537 · cache-1 19847 · cache-2 18507 · cache-3 17109
  (lo justo con pesos 2:1:1:1 → cache-0 40.000, los demás 20.000)

== 7 · Cada clave en 3 servidores: los 3 siguientes distintos del anillo (como Dynamo) ==
  copias por servidor (300.000 en total): cache-0 67970 · cache-1 86283 · cache-2 73006 · cache-3 72741

== 8 · ¿Importa la función de hash? El anillo con FNV-1a a secas, sin mezclador ==
  FNV a secas,  100 virtuales  el que menos   5360 · el que más  34650 · el más cargado lleva 1.39 veces lo justo
  FNV + mezcla,  100 virtuales el que menos  21225 · el que más  29768 · el más cargado lleva 1.19 veces lo justo
  FNV a secas, 1000 virtuales  el que menos  23030 · el que más  30060 · el más cargado lleva 1.20 veces lo justo
  FNV + mezcla, 1000 virtuales el que menos  24626 · el que más  25368 · el más cargado lleva 1.01 veces lo justo
```
