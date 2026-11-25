# 🔗 Cadena de suministro: Trivy, firmas con cosign y registro propio — material del curso

Código de estos vídeos del canal Cultura DevOps:

- [Cadena de suministro: Trivy, firmas con cosign y registro propio (curso completo)](https://youtu.be/qqkKyOif9GU) (miembros)
- [De DevOps a seguridad: la ruta blue team, con 3 laboratorios de defensa en casa](https://youtu.be/3d1bIlFQM_M)

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/qqkKyOif9GU**

---

> 🎬 Acompaña al vídeo **«Cadena de suministro: Trivy, firmas con cosign y registro propio (curso completo)»** del canal **Cultura DevOps** (solo miembros).

Código del curso **«Cadena de suministro»** de [Cultura DevOps](https://www.youtube.com/@culturadevops),
exclusivo para miembros del canal.

> Lo que despliegas, ¿es lo que construiste? Casi todo lo que rompe esa respuesta no da error: una
> etiqueta que alguien sobrescribe, un escáner que encuentra 4 críticas y sale con 0, un SBOM que
> esconde 32 vulnerabilidades, una firma que nadie verifica y un registro donde cualquiera sube.

Trivy **0.75.0**, cosign **v3.1.3**, syft **v1.54.1**, registry **3.1.2**.

## Cómo usar esto

Solo hace falta Docker y Python:

```bash
python ejecutar_todo.py     # levanta el registro, corre las 6 lecciones, lo limpia y escribe SALIDA.md
./desplegar.sh tienda:3.0   # el despliegue que verifica la firma (necesita el laboratorio levantado)
```

## Seguridad del laboratorio

- **Nada sale al registro público de transparencia (Rekor).** cosign y el «intruso» corren en la red
  `cadena-interna`, creada con `--internal`: sin salida a internet. `ejecutar_todo.py` lo comprueba
  antes de empezar y se niega a seguir si la red tiene salida. Además se firma con
  `--use-signing-config=false --tlog-upload=false`.
- Las claves de cosign se generan en cada ejecución en `claves/` con una frase de laboratorio. Están
  en `.gitignore`: no se suben a ningún sitio.
- Solo Trivy sale a internet, y solo para bajar su base de datos de vulnerabilidades.

## Las 6 lecciones

| # | qué se hace | la trampa |
|---:|---|---|
| 1 | subir y desplegar por etiqueta y por digest | `docker push` sobrescribe la etiqueta sin preguntar |
| 2 | `trivy image` y `--exit-code` | 48 vulnerabilidades, 4 críticas, y código 0 |
| 3 | SBOM con syft y con Trivy | el SBOM de syft escaneado por Trivy: 16 de 48 |
| 4 | `cosign sign` y `cosign verify` | la etiqueta se mueve a una imagen sin firmar y `docker run` la ejecuta |
| 5 | `desplegar.sh` | — verifica y arranca el digest verificado, no la etiqueta |
| 6 | registro con `htpasswd` | sin autenticación, cualquiera sobrescribe etiquetas |

## Lo que hay que saber de las medidas

- Los números de Trivy dependen de la fecha de su base de datos (está en `SALIDA.md`).
- La lección 3 no dice que syft esté mal: dice que Trivy busca por paquete de origen y que syft lo
  guarda en un campo propio (`syft:metadata:originPackage`) que Trivy no lee. El propio Trivy avisa:
  «Third-party SBOM may lead to inaccurate vulnerability detection».

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Docker (Trivy, cosign y el registro corren como contenedores).
- Python 3.10 o superior (para `ejecutar_todo.py`; solo biblioteca estándar salvo que se diga)

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-cadena-suministro
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-cadena-suministro/
├── app/
│   └── Dockerfile
├── .gitattributes
├── .gitignore
├── desplegar.sh
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
