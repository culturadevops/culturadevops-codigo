# Monta un SOC en tu casa con Wazuh — material del curso

Código de estos vídeos del canal Cultura DevOps:

- [Wazuh: 752 alertas antes de que entrara nadie (y qué es un SOC de verdad)](https://youtu.be/c3mvLmoK0ME) (miembros)
- [Docker decía «Up» cuatro días y el panel no funcionaba (Wazuh en Docker)](https://youtu.be/sjDJBZpHdz0) (miembros)
- [El agente decía «Active» y mentía: tu primer agente de Wazuh](https://youtu.be/X9s7CU-rl_s) (miembros)
- [Una línea de texto y 3 fases: cómo Wazuh decide que hay una alerta](https://youtu.be/llUywrLK_aI) (miembros)
- [1.313 alertas sin que pasara nada: los niveles de Wazuh y el ruido](https://youtu.be/ctcDYOeT5cA) (miembros)
- [Tu primera regla de Wazuh: el decoder, el XML roto y el fichero que nadie leía](https://youtu.be/m11MO8MyhBg) (miembros)
- [Toqué el fichero y esperé 5 minutos: nada. FIM en Wazuh, de verdad](https://youtu.be/W4O7g-Ax4r4) (miembros)
- [10 intentos por SSH y 167 alertas: solo una hay que mirar](https://youtu.be/arwY3dUDQHQ) (miembros)
- [Windows: el agente y Sysmon, donde está la telemetría buena](https://youtu.be/da-65jQn5CA) (miembros)
- [Respuesta activa: que bloquee la IP solo, y por qué asusta](https://youtu.be/epa-5jcjeaY) (miembros)
- [El escaneo de configuración tardó 0 segundos (y el panel se quedó en verde)](https://youtu.be/rnTWB0YAino) (miembros)
- [9,3 GB de catálogo y cero resultados: cuatro días con un módulo caído](https://youtu.be/CirJLEhcx6w) (miembros)
- [El 94% del disco de Wazuh no es tuyo: lo que cuesta de verdad](https://youtu.be/vMbVBoqGLLk) (miembros)
- [No has montado un escudo: has montado una memoria (lo que Wazuh no te da)](https://youtu.be/FGCmrDy9scg) (miembros)

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/c3mvLmoK0ME**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/sjDJBZpHdz0**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/X9s7CU-rl_s**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/llUywrLK_aI**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/ctcDYOeT5cA**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/m11MO8MyhBg**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/W4O7g-Ax4r4**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/arwY3dUDQHQ**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/da-65jQn5CA**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/epa-5jcjeaY**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/rnTWB0YAino**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/CirJLEhcx6w**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/vMbVBoqGLLk**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/FGCmrDy9scg**

---

Canal **Cultura DevOps** (YouTube) · curso exclusivo para miembros.

Un solo laboratorio (`laboratorio/`) con indexer, manager, dashboard y una víctima Ubuntu, todo en Docker. Las instrucciones completas y los tropiezos reales están en [`laboratorio/LEEME.md`](laboratorio/LEEME.md).

⛔ Todo ataque de las demos va contra el contenedor `lab-wazuh-victima` y contra nada más.

## Los vídeos

| # | carpeta | vídeo (título en YouTube) | id BD |
|---:|---|---|---:|
| 1 | [`01-que-vigila-un-soc-y-que-es-wazuh/`](01-que-vigila-un-soc-y-que-es-wazuh/) | Wazuh: 752 alertas antes de que entrara nadie (y qué es un SOC de verdad) | 61 |
| 2 | [`02-levantalo-en-docker/`](02-levantalo-en-docker/) | Docker decía «Up» cuatro días y el panel no funcionaba (Wazuh en Docker) | 62 |
| 3 | [`03-tu-primer-agente/`](03-tu-primer-agente/) | El agente decía «Active» y mentía: tu primer agente de Wazuh | 63 |
| 4 | [`04-el-camino-de-un-log/`](04-el-camino-de-un-log/) | Una línea de texto y 3 fases: cómo Wazuh decide que hay una alerta | 64 |
| 5 | [`05-niveles-de-regla-y-el-ruido/`](05-niveles-de-regla-y-el-ruido/) | 1.313 alertas sin que pasara nada: los niveles de Wazuh y el ruido | 65 |
| 6 | [`06-tu-primera-regla-y-decoder/`](06-tu-primera-regla-y-decoder/) | Tu primera regla de Wazuh: el decoder, el XML roto y el fichero que nadie leía | 66 |
| 7 | [`07-fim-quien-toco-ese-fichero/`](07-fim-quien-toco-ese-fichero/) | Toqué el fichero y esperé 5 minutos: nada. FIM en Wazuh, de verdad | 67 |
| 8 | [`08-fuerza-bruta-ssh/`](08-fuerza-bruta-ssh/) | 10 intentos por SSH y 167 alertas: solo una hay que mirar | 68 |
| 9 | [`09-windows-agente-y-sysmon/`](09-windows-agente-y-sysmon/) | Windows: el agente y Sysmon, donde está la telemetría buena | 69 |
| 10 | [`10-respuesta-activa/`](10-respuesta-activa/) | Respuesta activa: que bloquee la IP solo, y por qué asusta | 70 |
| 11 | [`11-sca-contra-cis/`](11-sca-contra-cis/) | El escaneo de configuración tardó 0 segundos (y el panel se quedó en verde) | 71 |
| 12 | [`12-vulnerabilidades-y-su-ruido/`](12-vulnerabilidades-y-su-ruido/) | 9,3 GB de catálogo y cero resultados: cuatro días con un módulo caído | 72 |
| 13 | [`13-lo-que-cuesta-de-verdad/`](13-lo-que-cuesta-de-verdad/) | El 94% del disco de Wazuh no es tuyo: lo que cuesta de verdad | 73 |
| 14 | [`14-lo-que-no-te-da/`](14-lo-que-no-te-da/) | No has montado un escudo: has montado una memoria (lo que Wazuh no te da) | 74 |

## Requisitos

- Docker con Compose (el laboratorio pide unos 2,2 GB de RAM y unos 8 GB de imágenes; la lección 13 lo mide).
- Bash para los `medir-*.sh`; Python 3.10+ para `medir.py`.
- Lección 9 (opcional): una máquina Windows de pruebas, el agente de Wazuh 4.9.2 (`.msi` de packages.wazuh.com), Sysmon (learn.microsoft.com/sysinternals) y la configuración `sysmonconfig-export.xml` de github.com/SwiftOnSecurity/sysmon-config.

## Cómo ejecutarlo

```bash
cd laboratorio
# 1. genera TUS certificados (no van en el repo)
docker compose -f generar-certificados.yml run --rm generador
# 2. levanta el SOC
docker compose up -d
```

Los certificados quedan en `config/wazuh_indexer_ssl_certs/`, que está en el `.gitignore`.

Las contraseñas del `docker-compose.yml` (`SecretPassword`, `kibanaserver`, `MyS3cr37P450r.*-`) y los hashes de `config/wazuh_indexer/internal_users.yml` son los de ejemplo de la documentación de Wazuh: sirven para el laboratorio y **hay que cambiarlos** en cualquier máquina que no sea de usar y tirar.

## Estructura

```
curso-wazuh/
├── 01-que-vigila-un-soc-y-que-es-wazuh/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 02-levantalo-en-docker/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 03-tu-primer-agente/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 04-el-camino-de-un-log/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 05-niveles-de-regla-y-el-ruido/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 06-tu-primera-regla-y-decoder/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 07-fim-quien-toco-ese-fichero/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 08-fuerza-bruta-ssh/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 09-windows-agente-y-sysmon/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 10-respuesta-activa/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 11-sca-contra-cis/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 12-vulnerabilidades-y-su-ruido/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 13-lo-que-cuesta-de-verdad/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 14-lo-que-no-te-da/
│   ├── EN-PANTALLA.md
│   └── README.md
├── laboratorio/
│   ├── config/
│   ├── windows/
│   ├── _tiempos.txt
│   ├── cronometrar-arranque.sh
│   ├── docker-compose.yml
│   ├── generar-certificados.yml
│   ├── LEEME.md
│   ├── MEDIDO.md
│   ├── medir-leccion-03.sh
│   ├── medir-leccion-06.sh
│   ├── medir-leccion-06b.sh
│   ├── medir-leccion-07.sh
│   ├── medir-leccion-10.sh
│   ├── medir-leccion-11-12.sh
│   ├── medir-leccion-11.sh
│   ├── medir-leccion-12.sh
│   ├── medir-lecciones.sh
│   ├── medir.py
│   ├── victima-instalar-agente.sh
│   └── victima-preparar.sh
└── .gitignore
```

Cada carpeta de lección trae su `README.md` y, si el vídeo enseña terminales, un `EN-PANTALLA.md` con los comandos y salidas tal cual aparecen en el vídeo.
