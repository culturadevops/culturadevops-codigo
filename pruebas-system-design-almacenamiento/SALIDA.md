# SALIDA — «System design: almacenamiento en bloque, en fichero o de objetos» (cultura-devops, vídeo 356)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-12 00:20:24Z`
- bloque: dispositivo loop con ext4 · fichero: NFSv4 (nfsd del kernel, export sync) · objetos: minio version RELEASE.2025-09-07T16-13-09Z (commit-id=07c3a429bfed433e49018cb0f78a52145d4bedeb), API S3 con boto3 1.35.36
- los tres sobre memoria (tmpfs): se mide el camino de acceso, no el disco. Cliente y servidores en la misma máquina, por la red de Docker, sin renders a la vez.
- una sola máquina; una sola conexión, operaciones una detrás de otra. NFS: periodo de gracia de 10 s, y se mide cuando ya pasó.

```
== 1 · Escribir 2.000 ficheros de 4 KB ==
$ python lab.py pequenos
  bloque             0.338 s → 5.925 op/s · con fsync de cada fichero
  fichero (NFS)      0.454 s → 4.408 op/s · con fsync de cada fichero
  objetos (S3)       2.539 s → 788 op/s

== 2 · Listarlos ==
$ python lab.py listar
  [vuelta 1]
  bloque             0.000 s · 2000 entradas · una llamada
  fichero (NFS)      0.002 s · 2000 entradas · una llamada
  objetos (S3)       0.101 s · 2000 objetos · 2 llamadas (1.000 por página)
  [vuelta 2]
  bloque             0.000 s · 2000 entradas · una llamada
  fichero (NFS)      0.000 s · 2000 entradas · una llamada
  objetos (S3)       0.093 s · 2000 objetos · 2 llamadas (1.000 por página)
  [vuelta 3]
  bloque             0.000 s · 2000 entradas · una llamada
  fichero (NFS)      0.001 s · 2000 entradas · una llamada
  objetos (S3)       0.089 s · 2000 objetos · 2 llamadas (1.000 por página)

== 3 · Renombrar la carpeta (fotos → fotos-2026) ==
$ python lab.py renombrar
  bloque             0.000 s · os.rename de la carpeta: 1 operación
  fichero (NFS)      0.000 s · os.rename de la carpeta: 1 operación
  objetos (S3)       2.668 s · no hay rename: 2000 copias + 2000 borrados

== 4 · Añadir 1.000 líneas de 35 bytes a un registro ==
$ python lab.py anadir
  bloque             0.003 s → 367.243 op/s · tamaño final 35.000 B
  fichero (NFS)      0.190 s → 5.261 op/s · tamaño final 35.000 B
  objetos (S3)       2.135 s → 468 op/s · tamaño final 35.000 B · no hay append: GET + PUT del objeto entero
  objetos (S3): bytes subidos para añadir 1.000 líneas de 35 B: 17.517.500

== 5 · Leer 1.000 ficheros sueltos de 4 KB ==
$ python lab.py leer
  bloque          leer un fichero de 4 KB: mediana 0.004 ms
  fichero (NFS)   leer un fichero de 4 KB: mediana 0.087 ms
  objetos (S3)    leer un objeto de 4 KB: mediana 1.002 ms
```
