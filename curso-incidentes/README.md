# 🚨 Un incidente de principio a fin: romperlo, diagnosticarlo y el postmortem — material del curso

Código del vídeo [«Un incidente de principio a fin: 5 incidentes provocados, diagnosticados y su postmortem»](https://youtu.be/ZVhHWxxg1Z0) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/ZVhHWxxg1Z0**

---

> 🎬 Acompaña al vídeo **«Un incidente de principio a fin: 5 incidentes provocados, diagnosticados y su postmortem»** del canal **Cultura DevOps** (solo miembros).

> 🎬 Acompaña al vídeo **«Un incidente de principio a fin: 5 incidentes provocados, diagnosticados y su postmortem»** del canal **Cultura DevOps** (solo miembros).

Código del curso de [Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros
del canal.

> Lo que no se puede leer en ningún libro: decidir **dónde mirar primero**. Cinco incidentes reales,
> provocados a propósito, recorridos enteros: la alerta salta sola, se diagnostica con datos (PromQL y
> LogQL contra la API, no a ojo), se arregla, y un script escribe el **postmortem sin culpables** con
> la línea de tiempo medida.

Usa el mismo stack que el curso «Observabilidad de verdad»: Prometheus 3.1, Loki 3.3 y Alertmanager 0.28.

## Cómo usar esto

```bash
docker compose version          # solo hace falta Docker y Python 3.10+
python ejecutar_todo.py         # levanta todo limpio, provoca los 5 incidentes, ~12 minutos
cd incidentes && python i3_certificado.py     # o uno solo (con el laboratorio levantado)
```

⚠️ **Tiempos comprimidos**: Prometheus mide y evalúa cada 5 s y las alertas piden 10-15 s. En
producción lo normal es 15-60 s y varios minutos de `for`. Lo que no cambia es el orden de los pasos.

## Los 5 incidentes

| # | script | el síntoma engañoso | la causa | la defensa |
|---:|---|---|---|---|
| 1 | `i1_disco_lleno.py` | «errores 500» | el modo depuración llenó el disco de auditoría | alerta de disco; depuración que caduca |
| 2 | `i2_fuga_de_memoria.py` | «se reinicia sola» | una caché sin tope; el núcleo la mata (oom, 137) | alerta predictiva con `predict_linear` |
| 3 | `i3_certificado.py` | «no se puede pagar» (domingo) | certificado renovado a mano | sonda HTTPS con días restantes |
| 4 | `i4_despliegue.py` | ninguno: **sin alerta** | SIGTERM ignorado como PID 1 + balanceador sin reintento | apagado limpio, reintento, `resolve` |
| 5 | `i5_consulta_lenta.py` | «solo en producción» | sin índice: 3 millones de filas | `pg_stat_statements`, `EXPLAIN`, `CONCURRENTLY` |

Cada incidente deja su postmortem en `postmortems/NN.md`: resumen, detección y mitigación medidas,
línea de tiempo, causa, qué funcionó, qué no, y acciones.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Docker con Compose.
- Python 3.10 o superior con `psycopg`.

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-incidentes
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-incidentes/
├── config/
│   ├── alertas.yml
│   ├── alertmanager.yml
│   ├── balanceador-bueno.conf
│   ├── balanceador-ingenuo.conf
│   ├── blackbox.yml
│   ├── prometheus.yml
│   ├── receptor.py
│   └── web-tls.conf
├── incidentes/
│   ├── comun.py
│   ├── i1_disco_lleno.py
│   ├── i2_fuga_de_memoria.py
│   ├── i3_certificado.py
│   ├── i4_despliegue.py
│   └── i5_consulta_lenta.py
├── postmortems/
│   ├── 01.md
│   ├── 02.md
│   ├── 03.md
│   ├── 04.md
│   └── 05.md
├── tienda/
│   ├── Dockerfile
│   └── tienda.py
├── .gitattributes
├── .gitignore
├── docker-compose.yml
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
