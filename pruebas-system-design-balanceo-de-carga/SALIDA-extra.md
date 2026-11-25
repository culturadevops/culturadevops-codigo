# SALIDA — balanceo de carga, segunda parte (cultura-devops, vídeo 345)

> Generado por `correr_extra.py`. **No se escribe a mano.**

- fecha: `2026-10-11 04:37:31Z` · mismo laboratorio que SALIDA.md

```
== 5 · Round robin con pesos: r1 y r2 pesan 5, r3 pesa 1 ==
$ HAProxy · balance roundrobin · weight 5/5/1
3000 bien · 0 fallos · p50 11ms · p99 202ms · total 3s
  reparto: r1 1364 · r2 1364 · r3 272

== 6 · random(2): dos réplicas al azar, y la que tenga menos conexiones ==
$ HAProxy · balance random(2)
3000 bien · 0 fallos · p50 11ms · p99 205ms · total 3.6s
  reparto: r1 1370 · r2 1263 · r3 367

== 7 · Sin chequeos, pero con option redispatch ==
$ carga -durante 12s   (HAProxy sin chequeos + option redispatch; a los 3 s muere el proceso de r2)
segundo  0:  137 bien ·   0 fallos
  segundo  1:  125 bien ·   0 fallos
  segundo  2:  140 bien ·   0 fallos
  segundo  3:   90 bien ·   0 fallos
  segundo  4:   94 bien ·   0 fallos
  segundo  5:   96 bien ·   0 fallos
  segundo  6:   93 bien ·   0 fallos
  segundo  7:   91 bien ·   0 fallos
  segundo  8:   97 bien ·   0 fallos
  segundo  9:   93 bien ·   0 fallos
  segundo 10:   92 bien ·   0 fallos
  segundo 11:   97 bien ·   0 fallos
  segundo 12:   10 bien ·   0 fallos
  1255 bien · 0 fallos · p50 13ms · p99 207ms · total 12.2s
  reparto: r1 559 · r2 137 · r3 559
  (r2 vuelve a arrancar para la prueba siguiente: en marcha)

== 8 · Hash por IP con 20 clientes, cada uno con su IP (30 peticiones cada uno) ==
$ 20 × carga -n 30 -c 1   (20 contenedores, de 10.77.21.100 a 10.77.21.119)
  reparto: r1 180 · r2 210 · r3 210

== 9 · nginx y un POST durante la caída ==
$ carga -post -durante 12s   (nginx pasivo; a los 3 s muere el proceso de r2)
segundo  0:  139 bien ·   0 fallos
  segundo  1:  130 bien ·   0 fallos
  segundo  2:  136 bien ·   0 fallos
  segundo  3:   93 bien ·   0 fallos
  segundo  4:   95 bien ·   0 fallos
  segundo  5:   94 bien ·   0 fallos
  segundo  6:   95 bien ·   0 fallos
  segundo  7:   95 bien ·   0 fallos
  segundo  8:   94 bien ·   0 fallos
  segundo  9:   96 bien ·   0 fallos
  segundo 10:   93 bien ·   0 fallos
  segundo 11:   95 bien ·   0 fallos
  segundo 12:   10 bien ·   0 fallos
  1265 bien · 0 fallos · p50 11ms · p99 202ms · total 12.2s
  reparto: r1 563 · r2 138 · r3 564
```
