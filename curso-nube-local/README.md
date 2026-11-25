# Tu nube local SIN licencias — material del curso

Código de estos vídeos del canal Cultura DevOps:

- [Tu laboratorio de AWS dejó de ser gratis: monta el recambio en un minuto](https://youtu.be/MHuaF-xIxQY) (miembros)
- [S3 en tu portátil: renombrar una carpeta no existe, y ahora vas a ver por qué](https://youtu.be/6h4-ggO7wqI) (miembros)
- [DynamoDB sin factura: Query y Scan parecen iguales con 3 filas (curso 3/8)](https://youtu.be/SsRnoCl6pT4) (miembros)
- [Recibir un mensaje no lo saca de la cola: lo esconde (curso 4/8)](https://youtu.be/DNJKqZHS_JA) (miembros)
- [SignatureDoesNotMatch: por fin alguien te dice por qué (curso 5/8)](https://youtu.be/XW4FejAIr4E) (miembros)
- [Tu Lambda no recibe peticiones: las va a buscar (curso 6/8)](https://youtu.be/ji8NSyNMsXU) (miembros)
- [El escalado de Lambda cabe en tres líneas, y la API de Docker es HTTP (7/8)](https://youtu.be/HY-etdQMv2A) (miembros)
- [Pruebas que arrancan siempre del mismo sitio, sin tarjeta (curso 8/8)](https://youtu.be/O_hH_x3wJi8) (miembros)

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/MHuaF-xIxQY**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/6h4-ggO7wqI**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/SsRnoCl6pT4**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/DNJKqZHS_JA**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/XW4FejAIr4E**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/ji8NSyNMsXU**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/HY-etdQMv2A**
> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/O_hH_x3wJi8**

---

Canal **Cultura DevOps** (YouTube) · curso exclusivo para miembros.

Se usa **nubecita**, el emulador de AWS en Go que se escribe en el curso de Golandia «Escribe tu propia nube en Go». Su código va en el repo hermano `golandia/curso-go-nube`. Aquí está el laboratorio que lo usa: quien habla con él es siempre la CLI oficial de AWS. Detalle y salidas literales en [`laboratorio/LEEME.md`](laboratorio/LEEME.md).

## Los vídeos

| # | carpeta | vídeo (título en YouTube) | id BD |
|---:|---|---|---:|
| 1 | [`01-tu-laboratorio-dejo-de-ser-gratis/`](01-tu-laboratorio-dejo-de-ser-gratis/) | Tu laboratorio de AWS dejó de ser gratis: monta el recambio en un minuto | 180 |
| 2 | [`02-s3-en-tu-portatil/`](02-s3-en-tu-portatil/) | S3 en tu portátil: renombrar una carpeta no existe, y ahora vas a ver por qué | 181 |
| 3 | [`03-dynamodb-sin-factura/`](03-dynamodb-sin-factura/) | DynamoDB sin factura: Query y Scan parecen iguales con 3 filas (curso 3/8) | 182 |
| 4 | [`04-colas-y-avisos/`](04-colas-y-avisos/) | Recibir un mensaje no lo saca de la cola: lo esconde (curso 4/8) | 183 |
| 5 | [`05-firmas-y-lo-que-aws-no-te-dice/`](05-firmas-y-lo-que-aws-no-te-dice/) | SignatureDoesNotMatch: por fin alguien te dice por qué (curso 5/8) | 184 |
| 6 | [`06-lambda-en-tu-maquina/`](06-lambda-en-tu-maquina/) | Tu Lambda no recibe peticiones: las va a buscar (curso 6/8) | 185 |
| 7 | [`07-que-los-levante-ella/`](07-que-los-levante-ella/) | El escalado de Lambda cabe en tres líneas, y la API de Docker es HTTP (7/8) | 186 |
| 8 | [`08-tus-pruebas-en-ci-sin-tarjeta/`](08-tus-pruebas-en-ci-sin-tarjeta/) | Pruebas que arrancan siempre del mismo sitio, sin tarjeta (curso 8/8) | 187 |

## Requisitos

- Docker.
- El código de nubecita (repo `curso-go-nube` de Golandia) para construir la imagen.
- La imagen oficial `amazon/aws-cli` (no hace falta instalar la CLI).

## Cómo ejecutarlo

```bash
docker network create curso-nube
docker build -t nubecita:curso <ruta-a>/curso-go-nube
docker build -t funcion-saludar:1 <ruta-a>/curso-go-nube/ejemplo-funcion
docker run -d --name nubecita --network curso-nube nubecita:curso -escuchar 0.0.0.0
cd laboratorio
MSYS_NO_PATHCONV=1 docker run --rm --network curso-nube -v "$(pwd):/lab" \
    --entrypoint sh amazon/aws-cli:latest /lab/correr.sh
```

En Git Bash de Windows, `MSYS_NO_PATHCONV=1` no es opcional (lo explica la lección 7) y la ruta se pasa con `$(pwd -W)`. El `LEEME.md` del laboratorio menciona rutas de la máquina donde se grabó (`<nubecita>`): cámbialas por la tuya.

## Estructura

```
curso-nube-local/
├── 01-tu-laboratorio-dejo-de-ser-gratis/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 02-s3-en-tu-portatil/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 03-dynamodb-sin-factura/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 04-colas-y-avisos/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 05-firmas-y-lo-que-aws-no-te-dice/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 06-lambda-en-tu-maquina/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 07-que-los-levante-ella/
│   ├── EN-PANTALLA.md
│   └── README.md
├── 08-tus-pruebas-en-ci-sin-tarjeta/
│   ├── EN-PANTALLA.md
│   └── README.md
├── laboratorio/
│   ├── estado/
│   ├── correr.sh
│   ├── lab.sh
│   ├── lab2.sh
│   ├── LEEME.md
│   ├── salida-real.txt
│   ├── semilla-real.json
│   └── semilla.json
└── .gitignore
```

Cada carpeta de lección trae su `README.md` y, si el vídeo enseña terminales, un `EN-PANTALLA.md` con los comandos y salidas tal cual aparecen en el vídeo.
