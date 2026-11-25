# Fuentes de la serie «¿X o Y? Lo medí» de herramientas (leídas 2026-11-05)

Lo medido sale de `<par>/SALIDA.md`. Aquí solo lo que NO se mide: encuestas y datos públicos.

## Stack Overflow Developer Survey 2026 — bases de datos (n = 12.061)

Uso («trabajo extenso el último año»): https://survey.stackoverflow.co/2026/technology/data/databases
Quieren usarla (desired) y admirada (admired): https://survey.stackoverflow.co/2026/technology/data/da-database
(Valores sacados del JSON-LD de las páginas; el primer bloque de da-database es «desired», el segundo «admired».)

| base | uso | quieren usarla | admirada |
|---|---|---|---|
| PostgreSQL | 57,9 % (6.984) | 43,9 % | 62,3 % |
| MySQL | 35,1 % (4.235) | 15,3 % | 38,2 % |
| Redis | 28,3 % (3.414) | 20,5 % | 51,0 % |
| Valkey | 5,0 % (603) | 5,7 % | 56,2 % |
| MariaDB | 20,3 % | 10,8 % | 43,3 % |
| SQLite | 42,1 % | 28,8 % | 56,4 % |

PostgreSQL es la base más admirada del año («PostgreSQL is the most admired database technology this year»).

## Proxies y servidores web

Nginx, Caddy, Traefik y HAProxy NO están en la encuesta 2026 (ni en databases ni en cloud-plat/da-platform).
En los vídeos de proxies no se cita ninguna cifra de uso.

## Contenedores (por si sale Docker o Podman)

https://survey.stackoverflow.co/2026/technology/data/cloud-plat (n = 10.889): Docker / Docker Compose 59,1 % de uso, Podman 13,0 %.
da-platform: quieren usarla Docker 38,4 %, Podman 10,7 %; admirada Docker 58,9 %, Podman 54,9 %.

## Licencias (de los propios proyectos, no medidas)

- Redis 8: AGPLv3 como opción, además de RSALv2 y SSPLv1 (anuncio de Redis, mayo de 2025). Valkey: BSD de 3 cláusulas,
  proyecto de la Linux Foundation, nacido en marzo de 2024 del último Redis BSD (7.2.4).
- Nginx: BSD de 2 cláusulas. Caddy: Apache 2.0. Traefik: MIT. HAProxy: GPLv2.
- PostgreSQL: licencia PostgreSQL (tipo MIT). MySQL Community: GPLv2 (Oracle).
