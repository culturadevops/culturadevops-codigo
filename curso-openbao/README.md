# 🔐 Secretos con OpenBao: sin contraseñas en el código — material del curso

Código del vídeo [«Secretos con OpenBao: sin contraseñas en el código, y las trampas que no dan error»](https://youtu.be/bdTykbwo15Q) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/bdTykbwo15Q**

---

> 🎬 Acompaña al vídeo **«Secretos con OpenBao: sin contraseñas en el código, y las trampas que no dan error»** del canal **Cultura DevOps** (solo miembros).

Código del curso **«Secretos con OpenBao»** de [Cultura DevOps](https://www.youtube.com/@culturadevops),
exclusivo para miembros del canal.

> OpenBao es el fork libre de Vault (licencia MPL, bajo la Linux Foundation). Guardar un secreto
> ahí es fácil; lo que no da error es lo que lo deja expuesto: el modo dev que lo pierde todo, una
> política que deja a la tienda leer la clave de los pagos, el token raíz dentro de la aplicación,
> la credencial que caduca a la hora y la auditoría que nadie activó.

OpenBao **2.7.1**, PostgreSQL **17**.

## Cómo usar esto

Solo Docker y Python:

```bash
python ejecutar_todo.py     # levanta OpenBao (dev y de verdad) y PostgreSQL, corre las 6 lecciones,
                            # lo borra todo y escribe SALIDA.md
```

- `config/bao.hcl` — el servidor de verdad: almacenamiento integrado (raft) y listener **sin TLS,
  solo para el laboratorio**.
- `politicas/` — las tres políticas de la lección 3: la mala, la que parece buena y la buena.
- Las claves de desbloqueo y los tokens se crean y se destruyen en cada ejecución.

## Las 6 lecciones

| # | qué se hace | la trampa |
|---:|---|---|
| 1 | `bao server -dev` | se reinicia el contenedor y el secreto ya no existe |
| 2 | `operator init` y `unseal` | las 5 claves se ven una vez; cada reinicio vuelve a sellar |
| 3 | políticas | `secret/*` deja leer los secretos de otros; `secret/tienda/*` da 403 en el propio |
| 4 | tokens y AppRole | el token raíz no caduca; uno normal dura 32 días |
| 5 | credenciales dinámicas de PostgreSQL | la aplicación que la lee al arrancar cae cuando caduca |
| 6 | auditoría | sin dispositivo, nadie sabe quién leyó qué |

## Lo que cambió en OpenBao 2.7 (y rompe tutoriales)

- El almacenamiento `file` ya no existe: «unknown storage type file». Se usa `raft`.
- La auditoría no se puede activar por la API: «cannot enable audit device via API». Se declara
  en la configuración y se recarga con `SIGHUP`, sin reiniciar y sin sellar.
- `disable_mlock` ya no se reconoce y da un aviso.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Docker.
- Python 3.10 o superior (para `ejecutar_todo.py`; solo biblioteca estándar salvo que se diga)

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-openbao
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-openbao/
├── config/
│   └── bao.hcl
├── politicas/
│   ├── tienda-casi.hcl
│   ├── tienda-mal.hcl
│   └── tienda.hcl
├── .gitattributes
├── .gitignore
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
