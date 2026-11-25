# 🏠 Tu propio GitHub y tu propio CI: Forgejo y Woodpecker — material del curso

Código del vídeo [«Tu propio GitHub y tu propio CI: Forgejo y Woodpecker, sin dejar la casa abierta (curso)»](https://youtu.be/C5d47ac6STw) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/C5d47ac6STw**

---

> 🎬 Acompaña al vídeo **«Tu propio GitHub y tu propio CI: Forgejo y Woodpecker, sin dejar la casa abierta (curso)»** del canal **Cultura DevOps** (solo miembros).

Código del curso **«Tu propio GitHub y tu propio CI»** de
[Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros del canal.

> Montar Forgejo y Woodpecker son dos `docker run`. Lo que no da error es lo que deja la casa
> abierta: el primero que se registra se queda de administrador, cualquiera puede darse de alta,
> las URL de clonado apuntan a localhost, el pipeline nunca arranca porque Forgejo no deja salir
> el webhook, y un secreto «tapado» en el log sale entero en base64.

Forgejo **13.0.5**, Woodpecker **3.18.1**.

## Cómo usar esto

Solo Docker y Python:

```bash
python ejecutar_todo.py     # levanta Forgejo y Woodpecker, recorre las 5 lecciones, lo borra todo
                            # y escribe SALIDA.md
```

- `lecciones.py` — el «navegador» del curso: rellena formularios, hace el login OAuth de Woodpecker
  contra Forgejo, activa el repositorio y sube commits. Corre dentro de la red de Docker
  (`cliente/Dockerfile`), para que Forgejo, Woodpecker y él vean las mismas direcciones.
- `ejecutar_todo.py` — reinicia Forgejo con la configuración de cada lección (variables
  `FORGEJO__seccion__CLAVE`, que son su `app.ini`).
- Usuarios, claves y tokens son de laboratorio y se destruyen al terminar (`estado.json` incluido).

## Las 5 lecciones

| # | qué se hace | la trampa |
|---:|---|---|
| 1 | instalar Forgejo | el primero que se registra es administrador |
| 2 | `DISABLE_REGISTRATION` | el alta está abierta por defecto |
| 3 | `ROOT_URL` | sin tocarla, la URL de clonado es `http://localhost:3000/...` |
| 4 | Woodpecker con OAuth y el webhook | Forgejo no deja salir el webhook a una red privada: 0 pipelines, ningún error |
| 5 | secretos de Woodpecker | el log tapa el valor exacto, pero no en base64 ni al revés |

## Lo que hay que saber

- La lección 4 se arregla con `FORGEJO__webhook__ALLOWED_HOST_LIST=private` porque aquí Woodpecker
  está en una red privada de Docker. En tu máquina, lo justo: el nombre o la IP de Woodpecker.
- En la lección 5, el filtro de imágenes de un secreto solo vale para pasos de **plugin**: Woodpecker
  rechaza el pipeline entero si un paso normal pide ese secreto.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Docker.
- Python 3.10 o superior con `requests`.

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-forgejo-woodpecker
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-forgejo-woodpecker/
├── cliente/
│   └── Dockerfile
├── .gitattributes
├── .gitignore
├── ejecutar_todo.py
├── lecciones.py
├── README.md
└── SALIDA.md
```
