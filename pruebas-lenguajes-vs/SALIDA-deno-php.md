# SALIDA — ¿Deno o PHP? (cultura-devops)

> Corrida del 2026-11-05 07:47. Regenerable con `python correr.py deno php`. ⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).

- deno: `deno 2.9.8 (stable, release, x86_64-unknown-linux-gnu)` — denoland/deno:2.9.8 (Deno.serve)
- php: `FrankenPHP v1.13.3 PHP 8.5.12 Caddy v2.11.7 h1:yj0Y4fYZGPkSvibBJ1sTWE33xC0fxztVyXEW5iIdUT4=` — dunglas/frankenphp:1.13.3-php8.5
- Docker `29.6.2`. Servidores con 2 CPU y 1g; `hey -c 16` con 4 CPU desde otro contenedor.
- /trabajo?n=20000: crea 20000 objetos, los mete en un mapa, los ordena y arma un JSON a mano. /suma?n=200000: multiplicar y módulo en un bucle.

## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)

| lenguaje | qué se cronometra | segundos |
|---|---|---|
| deno | copiar + deno check (comprobar tipos) | 1.1 |
| php | copiar el código (PHP no compila) | 0.7 |

## 2 · Lo que despliegas

| imagen | base | tamaño en disco |
|---|---|---|
| deno | denoland/deno:2.9.8 (Deno.serve) | 70.5 MiB |
| php | dunglas/frankenphp:1.13.3-php8.5 | 201.2 MiB |

## 0 · ¿Hacen lo mismo? (antes de medir)

- deno (1 hilo): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- deno serve --parallel: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php clásico (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker (FrankenPHP): total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual
- php worker + JIT: total 9990000, primeros ids [0, 1000, 2000, 3000, 4000]…, suma 99863963591 → igual

## 3 · Arranque: contenedor nuevo → primera respuesta 200 (mediana de 8) y memoria en reposo

| variante | 1ª respuesta (docker incluido) | «listo» (su propio reloj) | memoria en reposo |
|---|---|---|---|
| deno (1 hilo) | 247 ms | 5.3 ms | 20.0 MiB |
| deno serve --parallel | 241 ms | — | 30.4 MiB |
| php clásico (FrankenPHP) | 257 ms | — | 24.6 MiB |
| php worker (FrankenPHP) | 237 ms | 0.0 ms | 25.7 MiB |
| php worker + JIT | 231 ms | 0.0 ms | 26.2 MiB |

## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)

| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |
|---|---|---|
| deno (1 hilo) | 3.01 ms | 1.181 ms |
| deno serve --parallel | 3.19 ms | 1.179 ms |
| php clásico (FrankenPHP) | 11.55 ms | 0.670 ms |
| php worker (FrankenPHP) | 13.08 ms | 0.690 ms |
| php worker + JIT | 11.58 ms | 0.400 ms |

## 4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 264 | 261 | 60.7 ms | 67.9 ms | 79 MiB |
| deno serve --parallel | 477 | 489 | 14.8 ms | 84.2 ms | 149 MiB |
| php clásico (FrankenPHP) | 155 | 157 | 101.3 ms | 156.3 ms | 64 MiB |
| php worker (FrankenPHP) | 136 | 137 | 108.5 ms | 167.4 ms | 64 MiB |
| php worker + JIT | 155 | 154 | 102.2 ms | 159.6 ms | 62 MiB |

## 5 · Carga de CPU pura: /suma, a tope

`hey -c 16` desde otro contenedor; servidor con 2 CPU y 1g. «En frío»: los primeros 10 s tras arrancar. «Templado»: los 20 s siguientes.

| variante | peticiones/s en frío | peticiones/s templado | p50 | p99 | memoria máx. bajo carga |
|---|---|---|---|---|---|
| deno (1 hilo) | 839 | 839 | 19.0 ms | 19.9 ms | 27 MiB |
| deno serve --parallel | 1659 | 1672 | 11.2 ms | 12.9 ms | 39 MiB |
| php clásico (FrankenPHP) | 2553 | 2537 | 6.4 ms | 11.4 ms | 33 MiB |
| php worker (FrankenPHP) | 2607 | 2636 | 6.0 ms | 11.1 ms | 34 MiB |
| php worker + JIT | 4096 | 4073 | 3.9 ms | 7.2 ms | 34 MiB |

## 6 · Latencia de una petición sola: /trabajo

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 6.40 ms | 12.10 ms |
| deno serve --parallel | 5 | 6.00 ms | 10.60 ms |
| php clásico (FrankenPHP) | 5 | 14.20 ms | 20.80 ms |
| php worker (FrankenPHP) | 5 | 16.00 ms | 21.50 ms |
| php worker + JIT | 5 | 14.30 ms | 19.70 ms |

## 7 · Latencia de una petición sola: /suma

Un solo cliente a 5 peticiones/s (`hey -c 1 -q 5`), 20 s, tras 10 s de calentamiento a tope. Cada petición llega sola: no hay cola, es lo que tarda el servidor en atender una.

| variante | peticiones/s logradas | p50 | p99 |
|---|---|---|---|
| deno (1 hilo) | 5 | 1.60 ms | 6.20 ms |
| deno serve --parallel | 5 | 1.60 ms | 5.00 ms |
| php clásico (FrankenPHP) | 5 | 1.50 ms | 2.30 ms |
| php worker (FrankenPHP) | 5 | 1.40 ms | 2.00 ms |
| php worker + JIT | 5 | 1.00 ms | 2.30 ms |

