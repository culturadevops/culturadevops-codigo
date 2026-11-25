# SALIDA — ¿PHP o Java? (cultura-devops)

> Corrida del 2026-11-04 16:55. Regenerable con `python correr.py php java`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- php: `FrankenPHP v1.13.3 PHP 8.5.12 Caddy v2.11.7 h1:yj0Y4fYZGPkSvibBJ1sTWE33xC0fxztVyXEW5iIdUT4=` — dunglas/frankenphp:1.13.3-php8.5
- java: `openjdk version "25.0.5" 2026-10-20 LTS` — eclipse-temurin:25-jre + jar (com.sun.net.httpserver)
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| php | copiar el código (PHP no compila) | 0.8 |
| java | javac + jar | 1.2 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| php | dunglas/frankenphp:1.13.3-php8.5 | 201.2 MiB |
| java | eclipse-temurin:25-jre + jar (com.sun.net.httpserver) | 112.0 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- php clásico (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker + JIT: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos virtuales): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- java (hilos de plataforma): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| php clásico (FrankenPHP) | 251 ms | — | 24.5 MiB |
| php worker (FrankenPHP) | 244 ms | 0.0 ms | 25.6 MiB |
| php worker + JIT | 257 ms | 0.0 ms | 25.9 MiB |
| java (hilos virtuales) | 277 ms | 17.9 ms | 34.9 MiB |
| java (hilos de plataforma) | 254 ms | 18.6 ms | 33.8 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| php clásico (FrankenPHP) | 11.92 ms | 0.674 ms |
| php worker (FrankenPHP) | 15.52 ms | 0.671 ms |
| php worker + JIT | 12.01 ms | 0.401 ms |
| java (hilos virtuales) | 2.05 ms | 0.098 ms |
| java (hilos de plataforma) | 2.18 ms | 0.098 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| php clásico (FrankenPHP) | 144 | 152 | 102.4 ms | 161.7 ms | 66 MiB |
| php worker (FrankenPHP) | 133 | 133 | 110.4 ms | 170.5 ms | 63 MiB |
| php worker + JIT | 148 | 148 | 103.9 ms | 163.5 ms | 64 MiB |
| java (hilos virtuales) | 918 | 1013 | 15.6 ms | 19.9 ms | 296 MiB |
| java (hilos de plataforma) | 978 | 1037 | 15.2 ms | 23.4 ms | 289 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| php clásico (FrankenPHP) | 2502 | 2478 | 6.5 ms | 11.6 ms | 34 MiB |
| php worker (FrankenPHP) | 2494 | 2526 | 6.4 ms | 11.5 ms | 34 MiB |
| php worker + JIT | 3960 | 3978 | 4.1 ms | 7.4 ms | 34 MiB |
| java (hilos virtuales) | 13415 | 14330 | 0.5 ms | 21.6 ms | 58 MiB |
| java (hilos de plataforma) | 13351 | 14378 | 1.0 ms | 3.9 ms | 56 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| php clásico (FrankenPHP) | 5 | 13.30 ms | 17.80 ms |
| php worker (FrankenPHP) | 5 | 15.90 ms | 19.90 ms |
| php worker + JIT | 5 | 14.20 ms | 18.90 ms |
| java (hilos virtuales) | 5 | 3.20 ms | 9.20 ms |
| java (hilos de plataforma) | 5 | 3.30 ms | 6.40 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| php clásico (FrankenPHP) | 5 | 1.50 ms | 3.40 ms |
| php worker (FrankenPHP) | 5 | 1.40 ms | 2.80 ms |
| php worker + JIT | 5 | 1.10 ms | 2.20 ms |
| java (hilos virtuales) | 5 | 0.60 ms | 1.50 ms |
| java (hilos de plataforma) | 5 | 0.60 ms | 2.30 ms |

