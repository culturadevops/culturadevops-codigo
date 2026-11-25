# 💾 Restaurar, no copiar: copias de seguridad que de verdad funcionan — material del curso

Código del vídeo [«Copias de seguridad que de verdad se restauran: 9 ensayos destruyendo el original (curso completo)»](https://youtu.be/xktutfg3A7k) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/xktutfg3A7k**

---

> 🎬 Acompaña al vídeo **«Copias de seguridad que de verdad se restauran: 9 ensayos destruyendo el original (curso completo)»** del canal **Cultura DevOps** (solo miembros).

Código del curso **«Restaurar, no copiar»** de [Cultura DevOps](https://www.youtube.com/@culturadevops),
exclusivo para miembros del canal.

> Casi nadie prueba el restore. Una copia que no se ha restaurado nunca no es una copia: es una
> carpeta. Aquí cada lección destruye el original y mide lo que importa: **cuánto se tarda en volver
> (RTO) y cuánto se pierde por el camino (RPO)**. Y enseña la trampa que no da error: la copia de
> 20 bytes con código 0, la restauración que «termina bien» sin los usuarios, el archivado que falla
> en silencio, la retención que se come la última copia buena.

## Cómo usar esto

```bash
docker compose version         # Docker con compose: todo corre en contenedores
python ejecutar_todo.py        # levanta el laboratorio limpio, corre las 9 lecciones, regenera SALIDA.md
python ejecutar_todo.py --dejar
docker compose exec operador bash /curso/04_punto_en_el_tiempo.sh   # una sola lección
docker compose exec operador bash /curso/ensayo.sh                  # el simulacro
```

El laboratorio: `db` (Postgres 17 con el WAL archivado) y `operador` (cliente de Postgres 17, git,
age). La lección 5 habla con tu Docker desde un contenedor `docker:cli`: crea y borra contenedores,
volúmenes e imágenes con el prefijo `curso-vol-`, y nada más.

## Las 9 lecciones

| # | script | cómo se hace | la trampa |
|---:|---|---|---|
| 1 | `01_la_copia_vacia.sh` | `set -o pipefail` + tamaño mínimo | en cron, `pg_dump \| gzip` deja **20 bytes** con código 0 |
| 2 | `02_ensayo_cronometrado.sh` | destruir y medir | el RPO y el RTO que nadie tiene; `-j 4` casi no ayuda con una tabla |
| 3 | `03_lo_que_no_viaja.sh` | `pg_dumpall --globals-only`, `ON_ERROR_STOP` | restaura con código 0 y sin el rol de la aplicación |
| 4 | `04_punto_en_el_tiempo.sh` | copia base + WAL archivado | el archivado que falla en silencio (le pasó a este laboratorio) |
| 5 | `05_volumenes.sh` | copiar el volumen, con el servicio parado | `docker commit` no lleva el volumen; `down -v` lo borra |
| 6 | `06_git.sh` | `git bundle --all` + ignorados + hooks | el clon no trae ramas sin subir, stash, `.env` ni hooks |
| 7 | `07_secretos.sh` | la clave de `age` apartada | copia cifrada perfecta... y la clave estaba en la máquina |
| 8 | `08_retencion.sh` | guardar las N últimas **buenas** + alarma de edad | `find -mtime +7 -delete` deja 7 copias vacías y 0 buenas |
| 9 | `09_proyecto.sh` | `ensayo.sh` | — |

## El proyecto: ensayo.sh

Copia (con la huella de cada tabla tomada en la **misma instantánea** que `pg_dump`), restaura en un
servidor nuevo con `--exit-on-error`, verifica tabla por tabla y sale con **0** (la copia sirve),
**1** (restaura, pero hay tablas que no cuadran) o **2** (no hay copia que sirva). Se programa igual
que la copia: si el ensayo no sale con 0, no tienes copia.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Docker con Compose.
- Bash.
- Python 3.10 o superior (para `ejecutar_todo.py`; solo biblioteca estándar salvo que se diga)

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-restaurar-no-copiar
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-restaurar-no-copiar/
├── db-init/
│   └── 10-replicacion.sh
├── lecciones/
│   ├── 01_la_copia_vacia.sh
│   ├── 02_ensayo_cronometrado.sh
│   ├── 03_lo_que_no_viaja.sh
│   ├── 04_punto_en_el_tiempo.sh
│   ├── 05_volumenes.sh
│   ├── 06_git.sh
│   ├── 07_secretos.sh
│   ├── 08_retencion.sh
│   ├── 09_proyecto.sh
│   ├── comun.sh
│   └── ensayo.sh
├── operador/
│   └── Dockerfile
├── .gitattributes
├── .gitignore
├── docker-compose.yml
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
