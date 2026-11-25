# Git por dentro — material del curso

Código de estos vídeos del canal Cultura DevOps:

- [Una rama de Git pesa 41 bytes (y por eso ramificar es instantáneo)](https://youtu.be/vx0x53E3vSE) (miembros)
- [El índice de Git no es lo que crees (por eso confirmas otra versión)](https://youtu.be/reU_4y7rbjo) (miembros)
- [Un conflicto de Git son tres entradas en el índice (no marcas en el archivo)](https://youtu.be/5KrMOT_-Klw) (miembros)
- [En Git no pierdes el trabajo: pierdes el nombre que llevaba a él](https://youtu.be/f6sS2GhLrW0) (miembros)
- [Por qué limpiar un repositorio de Git puede dejarlo MÁS grande](https://youtu.be/M1eprbmDRX4) (miembros)
- [Los cuatro objetos de Git (construimos un commit a mano)](https://youtu.be/asqsWGqahj8) (miembros)

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/vx0x53E3vSE**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/reU_4y7rbjo**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/5KrMOT_-Klw**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/f6sS2GhLrW0**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/M1eprbmDRX4**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/asqsWGqahj8**

---

Canal **Cultura DevOps** (YouTube) · curso exclusivo para miembros.

Los scripts del laboratorio con que se grabó este curso **no se conservaron**. Lo que hay aquí es lo único que queda y es fiel: cada `EN-PANTALLA.md` trae los comandos, el código y las salidas tal cual salen en el vídeo, sacados automáticamente de su guion.

## Los vídeos

| # | carpeta | vídeo (título en YouTube) | id BD |
|---:|---|---|---:|
| 1 | [`01-los-cuatro-objetos/`](01-los-cuatro-objetos/) | Los cuatro objetos de Git (construimos un commit a mano) | 26 |
| 2 | [`02-ramas-y-head/`](02-ramas-y-head/) | Una rama de Git pesa 41 bytes (y por eso ramificar es instantáneo) | 17 |
| 3 | [`03-el-indice/`](03-el-indice/) | El índice de Git no es lo que crees (por eso confirmas otra versión) | 18 |
| 4 | [`04-merge-y-rebase/`](04-merge-y-rebase/) | Un conflicto de Git son tres entradas en el índice (no marcas en el archivo) | 19 |
| 5 | [`05-el-reflog/`](05-el-reflog/) | En Git no pierdes el trabajo: pierdes el nombre que llevaba a él | 20 |
| 6 | [`06-dentro-del-pack/`](06-dentro-del-pack/) | Por qué limpiar un repositorio de Git puede dejarlo MÁS grande | 21 |

## Requisitos

- Git (se grabó con git 2.55).
- Una terminal Bash (en Windows, Git Bash). Nada más.

## Cómo ejecutarlo

Crea una carpeta vacía y sigue el `EN-PANTALLA.md` de cada lección en orden:

```bash
mkdir lab-git && cd lab-git
# y copia los comandos de 01-los-cuatro-objetos/EN-PANTALLA.md
```

Los hashes de los blobs (contenido) te van a salir iguales; los de los commits no, porque llevan tu nombre y la fecha.

⚠️ La lección 6 (`06-dentro-del-pack`) midió en modo lectura un repositorio grande propio: haz esa parte sobre un repositorio tuyo o sobre un clon de usar y tirar.

## Estructura

```
curso-git/
├── 01-los-cuatro-objetos/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 02-ramas-y-head/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 03-el-indice/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 04-merge-y-rebase/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 05-el-reflog/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 06-dentro-del-pack/
│   ├── EN-PANTALLA.md
│   └── README.md
└── .gitignore
```

Cada carpeta de lección trae su `README.md` y, si el vídeo enseña terminales, un `EN-PANTALLA.md` con los comandos y salidas tal cual aparecen en el vídeo.
