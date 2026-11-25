# SALIDA — Restic vs Borg vs Kopia (vídeo 336)

Generado 2026-10-07 23:55 UTC con `python correr.py`. restic 0.19.1, borg 1.4.3, kopia 0.23.1; datos: biblioteca estándar de Python 3.12.

## 1 · Versiones y datos

### versiones

`$ restic/borg/kopia version`

```
restic 0.19.1 compiled with go1.26.4 on linux/amd64
borg 1.4.3
kopia 0.23.1
```

### los datos

`$ du -sh; nº de archivos`

```
27.8M	/d/proyecto
1261
```

## 2 · Crear el repositorio y la primera copia

### Restic

`$ restic init; restic backup`

```
ok
(1.ª copia en 5 s) · repo: 10.4M
```

### Borg

`$ borg init -e repokey; borg create ::c1`

```
ok
(1.ª copia en 6 s) · repo: 12.5M
```

### Kopia

`$ kopia repository create filesystem; kopia snapshot create`

```
Finished full maintenance.
ok
(1.ª copia en 1 s) · repo: 24.7M
```

## 3 · Un cambio pequeño y segunda copia (deduplicación)

### Restic

`$ restic backup`

```
Files:        1262 new,     0 changed,     0 unmodified
Dirs:          203 new,     0 changed,     0 unmodified
Added to the repository: 108.953 KiB (24.751 KiB stored)
ok
(2.ª copia en 1 s) · repo ahora: 10.4M
```

### Borg

`$ borg create --stats ::c2`

```
Original size      Compressed size    Deduplicated size
This archive:               25.57 MB             12.85 MB             17.82 kB
ok
(2.ª copia en 1 s) · repo ahora: 12.6M
```

### Kopia

`$ kopia snapshot create`

```
Created snapshot with root k0e8567c44ece89c3b76d7a8c93d9829c and ID ad66819017e693774b3aa31b276a2007 in 0s
ok
(2.ª copia en 1 s) · repo ahora: 24.8M
```

### espacio en disco tras 2 copias

`$ du -sh de cada repositorio`

```
Restic: 10.4M
Borg:   12.6M
Kopia:  24.8M
```

## 4 · Cifrado: ¿se ve el texto en el repositorio?

### grep del cambio en cada repo

`$ grep -rl 'cambio' /repo | wc -l`

```
Restic: 0
Borg:   0
Kopia:  0
(cada uno cifra por defecto: 0 = no aparece)
```

## 5 · Restaurar un solo archivo

### Restic

`$ restic dump latest .../os.py | tail -1`

```
cambio
```

### Borg

`$ borg extract ::c2 .../os.py`

```
cambio
```

### Kopia

`$ kopia restore <root>/os.py /tmp/os.py`

```
Restoring to local filesystem (/tmp/os.py) with parallelism=8...
Restored 1 files, 0 directories and 0 symbolic links (40.8 KB).

cambio
```

## 6 · Listar las copias

### Restic

`$ restic snapshots`

```
ID        Time                 Host          Tags        Paths           Size
-----------------------------------------------------------------------------------
d4ab7e9e  2026-10-07 23:54:45  9a9bddba84b4              /data/proyecto  24.366 MiB
7d8a74b1  2026-10-07 23:55:03  e4d9138f862f              /data/proyecto  24.382 MiB
-----------------------------------------------------------------------------------
Timestamps shown in UTC
2 snapshots
```

### Borg

`$ borg list`

```
c1                                   Wed, 2026-10-07 23:54:52 [9c3f09ece725e929f82b8f5a9cbc065d825b532af7d03b08d1c946114a50c09c]
c2                                   Wed, 2026-10-07 23:55:06 [0dc7d908526ea0cee0593d1d2eafc3bbf37d4a88f67d3bada2c36c08ac38aac6]
```

### Kopia

`$ kopia snapshot list`

```
root@943dd02d3b51:/data/proyecto
  2026-10-07 23:55:02 UTC k73fc0ed81e89c5e8d118b4f7d7b0e32a 25.6 MB drwxr-xr-x files:1261 dirs:202 (latest-2)
  2026-10-07 23:55:07 UTC k0e8567c44ece89c3b76d7a8c93d9829c 25.6 MB drwxr-xr-x files:1262 dirs:202 (latest-1,hourly-1,daily-1,weekly-1,monthly-1,annual-1)
```
