# Infraestructura como código de cero con OpenTofu — material del curso

Código del vídeo [«Infraestructura como código de cero con OpenTofu (curso completo, sin cuenta en ninguna nube)»](https://youtu.be/SQsC33Tx1eA) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/SQsC33Tx1eA**

---

Canal **Cultura DevOps** (YouTube) · curso exclusivo para miembros.

Acompaña al vídeo **«Infraestructura como código de cero con OpenTofu (curso completo, sin cuenta en ninguna nube)»** (id 126 en la fábrica).

Diez lecciones en un solo vídeo. Cada carpeta numerada es un proyecto de OpenTofu independiente, con el proveedor de Docker: **sin cuenta en ninguna nube**. Las mediciones y salidas literales están en `MEDIDO.md`.

⚠️ Los `terraform.tfstate` **no se suben**: en la lección 10 (`10-secretos/`) el estado guarda la contraseña en claro, que es justo lo que enseña el vídeo. Se generan al hacer `tofu apply`.

## Requisitos

- OpenTofu (se grabó con v1.12.5).
- Docker (proveedor `kreuzwerker/docker ~> 3.0`).

## Cómo ejecutarlo

```bash
cd 01-primer-recurso
tofu init
tofu plan
tofu apply
tofu destroy
```

Igual en `06-count`, `06-foreach`, `08-importar` y `10-secretos`. En Windows el proveedor necesita `host = "npipe:////./pipe/docker_engine"`. `medir-tiempos.sh` repite cada orden varias veces para cronometrarla.

## Estructura

```
curso-iac-opentofu-desde-cero/
├── 01-primer-recurso/
│   ├── .terraform.lock.hcl
│   └── main.tf
├── 06-count/
│   ├── .terraform.lock.hcl
│   └── main.tf
├── 06-foreach/
│   ├── .terraform.lock.hcl
│   └── main.tf
├── 08-importar/
│   ├── .terraform.lock.hcl
│   └── main.tf
├── 10-secretos/
│   ├── .terraform.lock.hcl
│   ├── cifrado.tf
│   └── main.tf
├── .gitignore
├── EN-PANTALLA.md
├── MEDIDO.md
└── medir-tiempos.sh
```

`EN-PANTALLA.md` tiene las 27 terminales del vídeo (9 comandos) con su salida medida, sacadas del guion del vídeo.
