# Contenedores por dentro — material del curso

Código del vídeo [«Contenedores por dentro: qué son de verdad (curso completo en un vídeo)»](https://youtu.be/XkLGstN78uM) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/XkLGstN78uM**

---

Canal **Cultura DevOps** (YouTube) · curso exclusivo para miembros.

Acompaña al vídeo **«Contenedores por dentro: qué son de verdad (curso completo en un vídeo)»** (id 128 en la fábrica).

Once lecciones en un solo vídeo. No hubo laboratorio guardado: lo que hay es `EN-PANTALLA.md`, con cada comando y su salida medida (espacios de nombres, overlay, cgroups, capacidades, podman sin root, red, volúmenes y señales).

## Requisitos

- Docker (se grabó con 29.6.2). Para la parte sin root, Podman.
- En Windows y macOS los contenedores corren dentro de una máquina Linux: lo que observas es de esa máquina.

## Cómo ejecutarlo

Sigue `EN-PANTALLA.md` en orden. Todos los comandos son de lectura o sobre contenedores de usar y tirar (`docker run --rm ...`).

## Estructura

```
curso-contenedores-por-dentro/
├── .gitignore
└── EN-PANTALLA.md
```

`EN-PANTALLA.md` tiene las 16 terminales del vídeo (13 comandos) con su salida medida, sacadas del guion del vídeo.
