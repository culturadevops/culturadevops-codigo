# ANEXO — repeticiones de la carga a tope (Redis contra Valkey)

> Corrida del 2026-11-05 14:23, bajo el candado. Mismo montaje que SALIDA.md; cada variante 3 veces, orden alternado (ida y vuelta), contenedor nuevo y el millón de claves cargado cada vez.

## Pipeline 1 · 1 SET por cada 10 GET · operaciones/s

| servidor | intento 1 | intento 2 | intento 3 | mediana | mín–máx |
|---|---|---|---|---|---|
| Redis | 318.272 | 315.526 | 315.726 | 315.726 | 315.526–318.272 |
| Redis · io-threads 2 | 304.674 | 303.531 | 304.153 | 304.153 | 303.531–304.674 |
| Valkey | 315.214 | 314.387 | 317.254 | 315.214 | 314.387–317.254 |
| Valkey · io-threads 2 | 290.510 | 296.093 | 293.586 | 293.586 | 290.510–296.093 |

## Pipeline 16 · 1 SET por cada 10 GET · operaciones/s

| servidor | intento 1 | intento 2 | intento 3 | mediana | mín–máx |
|---|---|---|---|---|---|
| Redis | 1.882.332 | 1.849.150 | 1.866.110 | 1.866.110 | 1.849.150–1.882.332 |
| Redis · io-threads 2 | 2.407.935 | 2.423.056 | 2.390.260 | 2.407.935 | 2.390.260–2.423.056 |
| Valkey | 1.822.545 | 1.819.998 | 1.812.087 | 1.819.998 | 1.812.087–1.822.545 |
| Valkey · io-threads 2 | 2.384.594 | 2.335.505 | 2.403.695 | 2.384.594 | 2.335.505–2.403.695 |

