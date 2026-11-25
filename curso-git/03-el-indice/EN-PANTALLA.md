# El índice de Git no es lo que crees (por eso confirmas otra versión) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. un proyecto limpio

```console
$ git status --short
(sin salida: limpio)
```

## 2. el índice de un proyecto limpio

```console
$ git ls-files --stage
100644 c3649c3b0183... 0  a.txt
100644 65b2df87f7df... 0  b.txt
100644 af17f6cc87e4... 0  c.txt
```

## 3. qué es .git/index

```console
$ file .git/index
.git/index: Git index, version 2, 3 entries

$ wc -c < .git/index
281
```

## 4. los primeros bytes

```console
$ od -An -c -N 12 .git/index
D   I   R   C  \0  \0  \0 002  \0  \0  \0 003
```

## 5. convertir el índice en objeto

```console
$ git write-tree
db4d7515b2a30dcc67853271dba177f2739e9b19

$ git cat-file -t db4d751
tree
```

## 6. y por dentro, lo de siempre

```console
$ git cat-file -p db4d751
100644 blob c3649c3b0183...  a.txt
100644 blob 65b2df87f7df...  b.txt
```

## 7. el mismo árbol que el del commit

```console
$ git rev-parse HEAD^{tree}
db4d7515b2a30dcc67853271dba177f2739e9b19
```

## 8. qué más guarda cada entrada

```console
$ git ls-files --debug a.txt
a.txt
  ctime: 1786974434:4632700
  mtime: 1786974434:5630400
  size: 5    flags: 0
```

## 9. predecir el hash antes de preparar

```console
$ echo 'alfa MODIFICADO' > a.txt
$ git hash-object a.txt
451180363ebd4be10c0fca98ce120ff74e212bc3
```

## 10. contar objetos antes y después

```console
$ find .git/objects -type f | wc -l
5

$ git add a.txt
$ find .git/objects -type f | wc -l
6
```

## 11. el índice ya apunta al nuevo

```console
$ git ls-files --stage a.txt
100644 451180363ebd... 0  a.txt
```

## 12. las dos comparaciones

```console
$ git diff --cached --stat
 a.txt | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

$ git diff --stat
(vacio: coinciden)
```

## 13. las dos letras que casi nadie lee

```console
$ echo 'alfa OTRA VEZ' > a.txt
$ git status --short
MM a.txt
```

## 14. las dos versiones, lado a lado

```console
$ git diff --cached a.txt
-alfa
+alfa MODIFICADO

$ git diff a.txt
-alfa MODIFICADO
+alfa OTRA VEZ
```

## 15. lo que se guardó, y lo que tienes delante

```console
$ git commit -m 'confirmo'
$ git show HEAD:a.txt
alfa MODIFICADO

$ cat a.txt
alfa OTRA VEZ
```

## 16. dos cambios en el disco

```console
$ cat multi.txt
linea 1 CAMBIADA
linea 2
linea 3 CAMBIADA
```

## 17. preparar solo un trozo

```console
$ git apply --cached --unidiff-zero parcial.patch

$ git diff --cached multi.txt
+linea 1 CAMBIADA
 linea 2
 linea 3
```

## 18. el contenido exacto del índice

```console
$ git show :multi.txt
linea 1 CAMBIADA
linea 2
linea 3

$ cat multi.txt
linea 1 CAMBIADA
linea 2
linea 3 CAMBIADA
```

## 19. quitar la línea, no el archivo

```console
$ git rm --cached c.txt
$ git ls-files --stage
100644 3dded5cbe1da... 0  a.txt
100644 65b2df87f7df... 0  b.txt
```

## 20. el archivo no se ha movido

```console
$ ls c.txt
c.txt

$ git status --short
D  c.txt
?? c.txt
```

## 21. excluido, y sigue apareciendo

```console
$ echo 'config.env' > .gitignore
$ echo 'secreto nuevo' > config.env
$ git status --short
 M config.env
?? .gitignore
```

## 22. ahora sí

```console
$ git rm --cached config.env
$ git status --short
D  config.env
?? .gitignore
```
