# Los cuatro objetos de Git (construimos un commit a mano) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. un repositorio recién nacido

```console
$ git init -b main .
$ git count-objects -v
count: 0
size: 0
in-pack: 0

$ ls .git/objects
info   pack
```

## 2. guardar contenido en el almacén

```console
$ echo 'hola mundo' > saludo.txt
$ git hash-object -w saludo.txt
24db42bb7b999597a72801da70efd5876059bc0b
```

## 3. preguntarle al objeto

```console
$ git cat-file -t 24db42b
blob

$ git cat-file -s 24db42b
11

$ git cat-file -p 24db42b
hola mundo
```

## 4. dónde acabó en el disco

```console
$ find .git/objects -type f
.git/objects/24/db42bb7b999597a72801da70efd5876059bc0b
```

## 5. el mismo hash, sin Git

```console
$ printf 'blob 11\0hola mundo\n' | sha1sum
24db42bb7b999597a72801da70efd5876059bc0b
```

## 6. el objeto en el disco, en crudo

```console
$ wc -c < saludo.txt
11

$ wc -c < .git/objects/24/db42bb...
27

$ od -An -tx1 -N 8 .git/objects/24/db42bb...
78 01 4b ca c9 4f 52 30
```

## 7. descomprimir el objeto sin Git

```console
$ python -c "import zlib,sys; \
$   print(zlib.decompress(open(sys.argv[1],'rb').read()))" \
$   .git/objects/24/db42bb...

b'blob 11\x00hola mundo\n'
```

## 8. dos archivos, un solo objeto

```console
$ echo 'hola mundo' > copia.txt
$ git hash-object -w copia.txt
24db42bb7b999597a72801da70efd5876059bc0b

$ find .git/objects -type f | wc -l
1
```

## 9. cambiar un solo bit

```console
$ # le damos la vuelta a 1 bit del ultimo byte
$ python romper.py .git/objects/24/db42bb...
cambiado 1 bit del ultimo byte
```

## 10. git fsck lo caza

```console
$ git fsck
error: inflate: data stream error
error: unable to unpack header of
  .git/objects/24/db42bb...
error: 24db42bb...: object corrupt or missing
```

## 11. construir el árbol

```console
$ git update-index --add \
$   --cacheinfo 100644,24db42bb...,saludo.txt

$ git write-tree
5b13221308ff4e24febcdb016e19e209ef473228
```

## 12. qué hay dentro del árbol

```console
$ git cat-file -p 5b13221
100644 blob 24db42bb…             saludo.txt

$ git cat-file -s 5b13221
38
```

## 13. fabricar el commit

```console
$ git commit-tree 5b13221 \
$   -m 'el primer commit, hecho a mano'
c3515ed15c316a151b486db28f1b44712d5d4f1b
```

## 14. un commit por dentro

```console
$ git cat-file -p c3515ed
tree 5b13221308ff4e24febcdb016e19e209ef473228
author cultura devops <a@b.c> 1786881600 +0000
committer cultura devops <a@b.c> 1786881600 +0000

el primer commit, hecho a mano
```

## 15. apuntar la rama al commit

```console
$ git update-ref refs/heads/main c3515ed

$ git log --oneline
c3515ed el primer commit, hecho a mano
```

## 16. y git show, igual

```console
$ git show --stat --oneline c3515ed
c3515ed el primer commit, hecho a mano
 saludo.txt         | 1 +
 1 file changed, 1 insertion(+)
```

## 17. la etiqueta también es un objeto

```console
$ git tag -a v1 -m 'primera version' c3515ed
$ git cat-file -p v1
object c3515ed15c316a151b486db28f1b44712d5d4f1b
type commit
tag v1
tagger cultura devops <a@b.c> 1786881600 +0000

primera version
```

## 18. el almacén completo

```console
$ git cat-file --batch-all-objects \
$   --batch-check='%(objecttype) %(objectsize) %(objectname)'

blob   11   24db42bb...
tree   38   5b132213...
commit 175  c3515ed1...
tag    131  b6d2c05f...
```
