# SALIDA — Restic (vídeo 325)

Generado 2026-10-07 20:44 UTC con `python correr.py`. Imagen restic/restic:latest. Datos: biblioteca estándar de python:3.12-slim.

## 1 · Versión y datos

### versión

`$ restic version`

```
restic 0.19.1 compiled with go1.26.4 on linux/amd64
```

### los datos

`$ du -sh /data/proyecto; find /data/proyecto -type f | wc -l`

```
27.8M	/data/proyecto
1261
```

## 2 · Crear el repositorio

### init

`$ restic init`

```
created restic repository 834875eb8e at /repo

Please note that knowledge of your password is required to access
the repository. Losing your password means that your data is
irrecoverably lost.
```

### qué hay dentro del repo

`$ ls /repo`

```
config
data
index
keys
locks
snapshots
```

## 3 · Primera copia

### backup 1

`$ restic backup /data/proyecto`

```
no parent snapshot found, will read all files

Files:        1261 new,     0 changed,     0 unmodified
Dirs:          203 new,     0 changed,     0 unmodified
Added to the repository: 24.855 MiB (9.269 MiB stored)

processed 1261 files, 24.366 MiB in 0:00
snapshot a66e18be saved
real 0.91
user 0.92
sys 0.30
```

## 4 · Cambio pequeño y segunda copia (deduplicación)

### backup 2

`$ restic backup /data/proyecto`

```
using parent snapshot a66e18be

Files:           1 new,     1 changed,  1260 unmodified
Dirs:            0 new,     2 changed,   201 unmodified
Added to the repository: 109.024 KiB (24.703 KiB stored)

processed 1262 files, 24.382 MiB in 0:00
snapshot 449b0680 saved
real 0.78
user 0.56
sys 0.02
```

### snapshots

`$ restic snapshots`

```
ID        Time                 Host        Tags        Paths           Size
---------------------------------------------------------------------------------
a66e18be  2026-10-07 20:43:45  servidor                /data/proyecto  24.366 MiB
449b0680  2026-10-07 20:43:47  servidor                /data/proyecto  24.382 MiB
---------------------------------------------------------------------------------
Timestamps shown in UTC
2 snapshots
```

### stats restore-size

`$ restic stats --mode restore-size`

```
scanning...
[0:00] 100.00%  2 / 2 snapshots, 1464 files, 24.366 MiB
Stats in restore-size mode:
     Snapshots processed:  2
        Total File Count:  2929
              Total Size:  48.748 MiB
```

### stats raw-data

`$ restic stats --mode raw-data`

```
scanning...
[0:00] 100.00%  2 / 2 snapshots, 1346 blobs, 9.240 MiB
Stats in raw-data mode:
     Snapshots processed:  2
        Total Blob Count:  1346
 Total Uncompressed Size:  25.003 MiB
              Total Size:  9.240 MiB
    Compression Progress:  100.00%
       Compression Ratio:  2.71x
Compression Space Saving:  63.04%
```

### tamaño real del repo

`$ du -sh /repo`

```
10.4M	/repo
```

## 5 · Cifrado: el texto no aparece en el repo

### grep en los datos

`$ grep -rl 'cambio de prueba' /data/proyecto | head -3`

```
/data/proyecto/os.py
```

### grep en el repo

`$ grep -rl 'cambio de prueba' /repo | wc -l`

```
0
```

### contraseña equivocada

`$ RESTIC_PASSWORD=otra restic snapshots`

```
codigo=12
Fatal: wrong password or no key found
```

## 6 · Restaurar un solo archivo

### borrar el archivo

`$ rm /data/proyecto/os.py`

```
codigo=1
ls: /data/proyecto/os.py: No such file or directory
```

### buscarlo

`$ restic find os.py`

```
Found matching entries in snapshot 449b0680 from 2026-10-07 20:43:47
/data/proyecto/os.py

Found matching entries in snapshot a66e18be from 2026-10-07 20:43:45
/data/proyecto/os.py
```

### restore --include

`$ restic restore latest --target /tmp/r --include /data/proyecto/os.py`

```
restoring snapshot 449b0680 of [/data/proyecto] at 2026-10-07 20:43:47.339472523 +0000 UTC by root@servidor to /tmp/r
Summary: Restored 3 / 1 files/dirs (39.883 KiB / 39.883 KiB) in 0:00
/tmp/r/data/proyecto/os.py
# cambio de prueba
```

### restaurar la versión vieja

`$ restic restore <snapshot 1> ... os.py`

```
restoring snapshot a66e18be of [/data/proyecto] at 2026-10-07 20:43:45.781857934 +0000 UTC by root@servidor to /tmp/v
Summary: Restored 3 / 1 files/dirs (39.864 KiB / 39.864 KiB) in 0:00
            nt._remove_dll_directory
        )
```

### dump a la salida

`$ restic dump latest /data/proyecto/os.py | tail -1`

```
# cambio de prueba
```

## 7 · Limpiar copias viejas

### snapshots antes

`$ restic snapshots`

```
ID        Time                 Host        Tags        Paths           Size
---------------------------------------------------------------------------------
a66e18be  2026-10-07 20:43:45  servidor                /data/proyecto  24.366 MiB
449b0680  2026-10-07 20:43:47  servidor                /data/proyecto  24.382 MiB
a0bef86d  2026-10-07 20:43:59  servidor                /data/proyecto  24.343 MiB
f62b6ecf  2026-10-07 20:44:01  servidor                /data/proyecto  24.343 MiB
0c29f540  2026-10-07 20:44:02  servidor                /data/proyecto  24.343 MiB
---------------------------------------------------------------------------------
Timestamps shown in UTC
5 snapshots
```

### forget --dry-run

`$ restic forget --keep-last 2 --dry-run`

```
Applying Policy: keep 2 latest snapshots
keep 2 snapshots:
ID        Time                 Host        Tags        Reasons        Paths           Size
------------------------------------------------------------------------------------------------
f62b6ecf  2026-10-07 20:44:01  servidor                last snapshot  /data/proyecto  24.343 MiB
0c29f540  2026-10-07 20:44:02  servidor                last snapshot  /data/proyecto  24.343 MiB
------------------------------------------------------------------------------------------------
Timestamps shown in UTC
2 snapshots

remove 3 snapshots:
ID        Time                 Host        Tags        Paths           Size
---------------------------------------------------------------------------------
a66e18be  2026-10-07 20:43:45  servidor                /data/proyecto  24.366 MiB
449b0680  2026-10-07 20:43:47  servidor                /data/proyecto  24.382 MiB
a0bef86d  2026-10-07 20:43:59  servidor                /data/proyecto  24.343 MiB
---------------------------------------------------------------------------------
Timestamps shown in UTC
3 snapshots

Would have removed the following snapshots:
{449b0680 a0bef86d a66e18be}
```

### forget --prune

`$ restic forget --keep-last 2 --prune`

```
Applying Policy: keep 2 latest snapshots
keep 2 snapshots:
ID        Time                 Host        Tags        Reasons        Paths           Size
------------------------------------------------------------------------------------------------
f62b6ecf  2026-10-07 20:44:01  servidor                last snapshot  /data/proyecto  24.343 MiB
0c29f540  2026-10-07 20:44:02  servidor                last snapshot  /data/proyecto  24.343 MiB
------------------------------------------------------------------------------------------------
Timestamps shown in UTC
2 snapshots

remove 3 snapshots:
ID        Time                 Host        Tags        Paths           Size
---------------------------------------------------------------------------------
a66e18be  2026-10-07 20:43:45  servidor                /data/proyecto  24.366 MiB
449b0680  2026-10-07 20:43:47  servidor                /data/proyecto  24.382 MiB
a0bef86d  2026-10-07 20:43:59  servidor                /data/proyecto  24.343 MiB
---------------------------------------------------------------------------------
Timestamps shown in UTC
3 snapshots

[0:00] 100.00%  3 / 3 files deleted
3 snapshots have been removed, running prune
loading all snapshots...
finding data that is still in use for 2 snapshots
[0:00] 100.00%  2 / 2 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  10 / 10 packs processed

to repack:           109 blobs / 115.871 KiB
this removes:          3 blobs / 12.796 KiB
to delete:             8 blobs / 37.475 KiB
total prune:          11 blobs / 50.271 KiB
remaining:          1347 blobs / 9.229 MiB
unused size after prune: 11.658 KiB (0.12% of remaining size)

repacking packs
[0:00] 100.00%  1 / 1 packs repacked
rebuilding index
[0:00] 100.00%  6 / 6 indexes processed
[0:00] 100.00%  6 / 6 old indexes deleted
removing 5 old packs
[0:00] 100.00%  5 / 5 files deleted
done
```

### snapshots después

`$ restic snapshots`

```
ID        Time                 Host        Tags        Paths           Size
---------------------------------------------------------------------------------
f62b6ecf  2026-10-07 20:44:01  servidor                /data/proyecto  24.343 MiB
0c29f540  2026-10-07 20:44:02  servidor                /data/proyecto  24.343 MiB
---------------------------------------------------------------------------------
Timestamps shown in UTC
2 snapshots
```

### check

`$ restic check`

```
using temporary cache in /tmp/restic-check-cache-3245389588
create exclusive lock for repository
load indexes
check all packs
check snapshots, trees and blobs
[0:00] 100.00%  2 / 2 snapshots
no errors were found
```

## 8 · La trampa: el hostname (contenedores sin --hostname)

### backup con hostname aleatorio 1

`$ docker run (sin --hostname) restic backup`

```
8990fe097301
ok
```

### backup con hostname aleatorio 2

`$ docker run (sin --hostname) restic backup`

```
35f92f543062
no parent snapshot found, will read all files

Files:        1262 new,     0 changed,     0 unmodified
```

### forget agrupa por host

`$ restic forget --keep-last 1 --dry-run`

```
Applying Policy: keep 1 latest snapshots
keep 1 snapshots:
1 snapshots
keep 1 snapshots:
1 snapshots
keep 1 snapshots:
1 snapshots
keep 1 snapshots:
1 snapshots
```

### la solución: --group-by paths

`$ restic forget --keep-last 1 --group-by paths --dry-run`

```
Applying Policy: keep 1 latest snapshots
keep 1 snapshots:
1 snapshots
remove 3 snapshots:
3 snapshots
Would have removed the following snapshots:
```
