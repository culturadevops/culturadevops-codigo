# Azure Fundamentals (AZ-900) — material del curso

Código de estos vídeos del canal Cultura DevOps:

- [Azure Fundamentals 1: conceptos de nube, con precios reales (AZ-900)](https://youtu.be/ZX4Kd6AVBB4) (miembros)
- [Azure Fundamentals 2: arquitectura y servicios, funcionando (AZ-900)](https://youtu.be/g3o3nLuRjOE) (miembros)
- [Azure Fundamentals 3: gobierno, costes y el examen AZ-900](https://youtu.be/-L_y-C83kuQ) (miembros)

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/ZX4Kd6AVBB4**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/g3o3nLuRjOE**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/-L_y-C83kuQ**

---

Canal **Cultura DevOps** (YouTube) · curso exclusivo para miembros.

Curso **casi todo teoría** (preparación del examen AZ-900). No hay código: solo las pocas terminales que salen en pantalla (la API pública de precios, Azurite y `sqlcmd` en el bloque 2) y los precios que se consultaron al grabar (`precios-medidos.txt`).

## Los vídeos

| # | carpeta | vídeo (título en YouTube) | id BD |
|---:|---|---|---:|
| 1 | [`01-conceptos-de-nube/`](01-conceptos-de-nube/) | Azure Fundamentals 1: conceptos de nube, con precios reales (AZ-900) | 112 |
| 2 | [`02-arquitectura-y-servicios/`](02-arquitectura-y-servicios/) | Azure Fundamentals 2: arquitectura y servicios, funcionando (AZ-900) | 113 |
| 3 | [`03-gestion-y-gobierno/`](03-gestion-y-gobierno/) | Azure Fundamentals 3: gobierno, costes y el examen AZ-900 | 114 |

## Requisitos

- Para el bloque 2: Docker (Azurite) y Azure CLI. Sin cuenta de Azure.

## Cómo ejecutarlo

Sigue `02-arquitectura-y-servicios/EN-PANTALLA.md`. Los precios cambian: `precios-medidos.txt` es una foto del día de la grabación.

## Estructura

```
curso-azure-fundamentals/
├── 01-conceptos-de-nube/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 02-arquitectura-y-servicios/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 03-gestion-y-gobierno/
│   ├── EN-PANTALLA.md
│   └── README.md
├── .gitignore
└── precios-medidos.txt
```

Cada carpeta de lección trae su `README.md` y, si el vídeo enseña terminales, un `EN-PANTALLA.md` con los comandos y salidas tal cual aparecen en el vídeo.
