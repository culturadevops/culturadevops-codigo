# Terraform 2026 desde cero — material del curso

Código de estos vídeos del canal Cultura DevOps:

- [Terraform 2026 desde cero: tu primera infraestructura sin cuenta en ninguna nube](https://youtu.be/NFLxI-S1Mp0) (miembros)
- [Leer un plan de Terraform: el aviso de que va a destruir algo](https://youtu.be/svqVWSA2jb0) (miembros)
- [El estado de Terraform: el día que un plan borró mi contenedor](https://youtu.be/A2MbImse2FM) (miembros)
- [Variables en Terraform: sensitive no esconde tu secreto](https://youtu.be/02Ez9_1K_WA) (miembros)
- [count o for_each en Terraform: el error que destruye lo que nadie tocó](https://youtu.be/lPhh0Wwrc-M) (miembros)
- [Módulos y versiones en Terraform: el archivo que tienes que subir al repositorio](https://youtu.be/uSWxhiFTMpo) (miembros)
- [Cambiar Terraform sin destruir nada: moved, import y removed](https://youtu.be/Ixdz2Vg8x10) (miembros)
- [Pruebas en Terraform: el test que pasa sin ejecutar nada](https://youtu.be/bmbZQrinO3c) (miembros)

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/NFLxI-S1Mp0**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/svqVWSA2jb0**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/A2MbImse2FM**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/02Ez9_1K_WA**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/lPhh0Wwrc-M**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/uSWxhiFTMpo**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/Ixdz2Vg8x10**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/bmbZQrinO3c**

---

Canal **Cultura DevOps** (YouTube) · curso exclusivo para miembros.

Ocho lecciones sobre los mismos proyectos de `laboratorio/`, con el proveedor de Docker: **sin cuenta en ninguna nube**. Todas las cifras y salidas literales están en [`laboratorio/MEDIDO.md`](laboratorio/MEDIDO.md) y en los `salida-*.txt` de cada proyecto.

⚠️ Los `terraform.tfstate` no se suben (se generan con `terraform apply`). Los `.terraform.lock.hcl` sí, a propósito.

## Los vídeos

| # | carpeta | vídeo (título en YouTube) | id BD |
|---:|---|---|---:|
| 1 | [`01-tu-primera-infraestructura/`](01-tu-primera-infraestructura/) | Terraform 2026 desde cero: tu primera infraestructura sin cuenta en ninguna nube | 250 |
| 2 | [`02-leer-un-plan/`](02-leer-un-plan/) | Leer un plan de Terraform: el aviso de que va a destruir algo | 251 |
| 3 | [`03-el-estado/`](03-el-estado/) | El estado de Terraform: el día que un plan borró mi contenedor | 252 |
| 4 | [`04-variables-y-secretos/`](04-variables-y-secretos/) | Variables en Terraform: sensitive no esconde tu secreto | 253 |
| 5 | [`05-count-for-each-y-dependencias/`](05-count-for-each-y-dependencias/) | count o for_each en Terraform: el error que destruye lo que nadie tocó | 254 |
| 6 | [`06-modulos-y-versiones/`](06-modulos-y-versiones/) | Módulos y versiones en Terraform: el archivo que tienes que subir al repositorio | 255 |
| 7 | [`07-cambiar-sin-destruir/`](07-cambiar-sin-destruir/) | Cambiar Terraform sin destruir nada: moved, import y removed | 256 |
| 8 | [`08-pruebas-y-ci/`](08-pruebas-y-ci/) | Pruebas en Terraform: el test que pasa sin ejecutar nada | 257 |

## Requisitos

- Terraform (se grabó con v1.16.2; `09-query` usa `terraform query`, que solo traen las versiones recientes).
- Docker (proveedor `kreuzwerker/docker` v3.9.0).

## Cómo ejecutarlo

```bash
cd laboratorio/01-primer-apply
terraform init
terraform plan
terraform apply
terraform destroy
```

En Windows el proveedor necesita `host = "npipe:////./pipe/docker_engine"`. `laboratorio/crono.sh` repite una orden cinco veces y da la media en milisegundos.

## Estructura

```
curso-terraform-2026/
├── 01-tu-primera-infraestructura/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 02-leer-un-plan/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 03-el-estado/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 04-variables-y-secretos/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 05-count-for-each-y-dependencias/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 06-modulos-y-versiones/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 07-cambiar-sin-destruir/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 08-pruebas-y-ci/
│   ├── EN-PANTALLA.md
│   └── README.md
├── laboratorio/
│   ├── 01-primer-apply/
│   ├── 02-plan/
│   ├── 04-variables/
│   ├── 04b-efimera/
│   ├── 05-repetir/
│   ├── 05b-paralelo/
│   ├── 05c-dependencias/
│   ├── 05d-mapa/
│   ├── 06-modulos/
│   ├── 07-refactor/
│   ├── 07b-id-corto/
│   ├── 08-pruebas/
│   ├── 08b-validate/
│   ├── 09-query/
│   ├── crono.sh
│   └── MEDIDO.md
└── .gitignore
```

Cada carpeta de lección trae su `README.md` y, si el vídeo enseña terminales, un `EN-PANTALLA.md` con los comandos y salidas tal cual aparecen en el vídeo.
