# 🌐 Redes para gente de DevOps: DNS, NAT, TLS y el «en mi máquina sí» — material del curso

Código del vídeo [«Redes para gente de DevOps: 7 trampas que no dan error, en contenedores (curso completo)»](https://youtu.be/vElcYsyq7oI) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/vElcYsyq7oI**

---

> 🎬 Acompaña al vídeo **«Redes para gente de DevOps: 7 trampas que no dan error, en contenedores (curso completo)»** del canal **Cultura DevOps** (solo miembros).

Código del curso de [Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros
del canal.

> No es un curso de redes de academia. Es el trozo de redes que rompe despliegues, cada pieza
> reproducida en un laboratorio de contenedores para **verla fallar**: el puerto publicado que da
> respuesta vacía, el nginx que manda tus peticiones a OTRO servicio tras un redespliegue, el
> certificado que curl acepta y Go rechaza, y el MTU que deja pasar lo pequeño y cuelga lo grande.

## Cómo usar esto

```bash
docker version                # solo hace falta Docker
python ejecutar_todo.py       # construye la imagen, corre las 7 lecciones y regenera SALIDA.md
```

Cada lección corre en un contenedor `docker:cli` que habla con tu Docker: crea redes y contenedores
con el prefijo `red-` y los borra al terminar. La lección 4 usa además `golang:1.26`.

## Las 7 lecciones

| # | script | la trampa | lo correcto |
|---:|---|---|---|
| 1 | `01_escuchar.sh` | escucha en `127.0.0.1`: con `-p`, «Empty reply from server» | `0.0.0.0` dentro; `-p 127.0.0.1:…` fuera si no es público |
| 2 | `02_dns_de_docker.sh` | la red por defecto no resuelve nombres; dos redes no se ven | una red tuya; `--internal` para no salir |
| 3 | `03_cache_dns.sh` | nginx resuelve una vez: tras redesplegar, habla con **otro servicio** y da 200 | `resolver 127.0.0.11 valid=…` + variable |
| 4 | `04_tls.sh` | cadena incompleta, sin SAN, caducado, nombre equivocado; **sin SAN curl dice ok, Go no** | cadena completa, SAN, `-checkend` |
| 5 | `05_mtu.sh` | ICMP filtrado: lo pequeño va, lo grande se cuelga con **HTTP 200 y 0 bytes** | dejar pasar ese ICMP, o `TCPMSS --clamp-mss-to-pmtu` |
| 6 | `06_ip_del_cliente.sh` | detrás de un proxy todos son el proxy; `X-Forwarded-For` lo escribe cualquiera | que lo escriba tu proxy, y fiarse solo de él |
| 7 | `07_proyecto.sh` | — | `diagnostico.sh` |

## El proyecto: diagnostico.sh

```bash
bash lecciones/diagnostico.sh https://api.tienda.test/ --ca raiz.pem
```

Recorre las capas de abajo arriba (DNS, TCP, TLS, HTTP y el cuerpo entero), para en la primera que
falla y sale con su número: 0 todo bien, 1 DNS, 2 TCP, 3 TLS, 4 HTTP, 5 la respuesta llega a medias.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Docker.
- Python 3.10 o superior (para `ejecutar_todo.py`; solo biblioteca estándar salvo que se diga)

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-redes-devops
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-redes-devops/
├── cliente-go/
│   ├── go.mod
│   └── main.go
├── imagen/
│   └── Dockerfile
├── lecciones/
│   ├── 01_escuchar.sh
│   ├── 02_dns_de_docker.sh
│   ├── 03_cache_dns.sh
│   ├── 04_tls.sh
│   ├── 05_mtu.sh
│   ├── 06_ip_del_cliente.sh
│   ├── 07_proyecto.sh
│   ├── certs.sh
│   ├── comun.sh
│   └── diagnostico.sh
├── .gitattributes
├── .gitignore
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
