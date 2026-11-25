## Medición (2026-11-05 10:50) · 15 arranques en frío y 30 en caliente por variante

Columnas: total = `docker run` → 1.ª respuesta (incluye Docker) · 1.ª Duration = lo que el RIE pone en el REPORT
de la 1.ª invocación (ahí dentro va el INIT, porque el RIE inicia en la 1.ª llamada) · caliente = invocaciones 2..N.

| variante | total frío p50 (min-max) ms | INIT REPORT p50 ms | 1.ª Duration p50 ms | caliente Duration p50 ms | caliente ida y vuelta p50 ms | memoria contenedor MiB |
|---|---|---|---|---|---|---|
| python · simple | 234 (223-357) | 27.9 | 29.0 | 0.97 | 13.87 | 15.3 |
| node · simple | 238 (223-358) | 29.3 | 31.7 | 0.55 | 12.10 | 21.8 |
| python · sdk | 372 (356-622) | 164.6 | 165.6 | 0.95 | 14.91 | 51.1 |
| node · sdk | 311 (293-334) | 97.1 | 98.5 | 0.52 | 14.51 | 41.9 |

Crudos (total frío ms, en orden de ronda):
  python·simple: 357 227 228 227 234 232 250 244 255 242 234 249 226 223 236
  node·simple: 358 234 269 238 236 239 242 246 223 238 236 235 230 228 247
  python·sdk: 622 406 381 366 369 383 356 372 379 371 364 368 368 380 419
  node·sdk: 313 321 319 296 297 293 330 306 315 334 307 311 329 296 304
Crudos (INIT REPORT ms):
  python·simple: 88.7 28.3 27.5 27.2 27.1 27.9 28.6 28.4 29.2 28.2 27.0 28.0 27.0 27.0 27.6
  node·simple: 122.7 30.3 33.0 30.9 29.3 28.4 31.6 31.2 29.2 27.3 29.0 28.9 29.5 27.5 28.9
  python·sdk: 410.4 185.6 158.7 161.8 168.8 172.3 161.5 164.6 168.8 160.7 161.1 159.2 157.8 169.1 179.2
  node·sdk: 121.5 95.4 99.9 90.4 96.9 97.4 95.3 97.0 101.5 94.8 98.1 101.5 97.1 97.2 95.7
Crudos (1.ª Duration ms):
  python·simple: 90.4 29.5 28.6 28.3 28.2 29.0 29.8 29.6 30.4 29.2 28.1 29.1 28.1 28.2 28.8
  node·simple: 124.0 31.7 39.1 35.3 33.6 29.6 32.8 35.7 30.4 28.7 30.2 33.2 30.7 28.7 30.0
  python·sdk: 411.6 186.9 159.8 163.2 170.0 173.4 162.8 165.6 170.0 161.9 162.6 160.7 158.9 170.3 180.4
  node·sdk: 123.5 96.8 101.3 91.6 99.4 99.0 96.6 98.3 102.9 97.2 99.4 102.8 98.4 98.5 97.8
