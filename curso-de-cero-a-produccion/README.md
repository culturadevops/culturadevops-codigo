# 🧵 De cero a producción: un proyecto entero, cosiendo lo que ya sabes — material del curso

Código del vídeo [«De cero a producción: un proyecto entero, cosiendo lo que ya sabes (curso completo)»](https://youtu.be/pjcAj6wvqaA) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/pjcAj6wvqaA**

---

> 🎬 Acompaña al vídeo **«De cero a producción: un proyecto entero, cosiendo lo que ya sabes (curso completo)»** del canal **Cultura DevOps** (solo miembros).

Código del curso de [Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros
del canal. **El capstone**: no enseña nada nuevo. Cose lo que el canal ya tiene suelto, que es la queja
del alumno que ha visto seis cursos y no sabe montar UNA cosa.

> Una aplicación pequeña (la tienda del curso de incidentes), desde el repositorio vacío hasta que
> atiende tráfico con su certificado, sus alertas, su copia probada y sus despliegues sin cortar. En
> cada paso, la trampa que no da error y el curso donde ese trozo está a fondo.

⚠️ «Producción» es **el Docker de esta máquina**, levantado con OpenTofu y el proveedor de Docker. El
certificado es de una CA propia, no de un dominio público. Las piezas que vienen de otros cursos están
copiadas tal cual (ver `herramientas/DE_DONDE_SALE.md`).

```bash
python paso_a_paso.py          # los 9 pasos, de cero, y SALIDA.md (luego lo destruye)
python paso_a_paso.py --dejar
```

| paso | la trampa | a fondo |
|---:|---|---|
| 1 | un `.env` borrado sigue en la historia de git | Git por dentro |
| 2 | la imagen de los tutoriales: 421 MB y root | Contenedores por dentro |
| 3 | la clave en claro en `terraform.tfstate`, aunque sea `sensitive` → estado cifrado | OpenTofu desde cero |
| 4 | las variables de entorno las enseña `docker inspect` → `_FILE` | Terraform 2026: variables y secretos |
| 5 | la tienda no contestaba a HEAD: lo encontró `diagnostico.sh` | Redes para gente de DevOps |
| 6 | que Prometheus vea las dos réplicas y tenga sus alertas | Observabilidad · Incidentes |
| 7 | la copia, probada con `ensayo.sh` contra producción | Restaurar, no copiar |
| 8 | `tofu apply -replace` réplica a réplica con tráfico: 0 fallos | Un incidente de principio a fin |
| 9 | la lista, comprobada por código: 9 de 9 o no está listo | todos |

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Docker.
- OpenTofu.
- Python 3.10 o superior con `psycopg`.

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-de-cero-a-produccion
python paso_a_paso.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-de-cero-a-produccion/
├── app/
│   ├── Dockerfile
│   ├── Dockerfile.ingenuo
│   └── tienda.py
├── herramientas/
│   ├── DE_DONDE_SALE.md
│   ├── diagnostico.sh
│   ├── Dockerfile.cliente
│   └── ensayo.sh
├── infra/
│   ├── alertas.yml
│   ├── main.tf
│   ├── prometheus.yml
│   └── proxy.conf
├── .gitattributes
├── .gitignore
├── paso_a_paso.py
├── README.md
└── SALIDA.md
```
