# Una rama de Git pesa 41 bytes (y por eso ramificar es instantáneo) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. tres commits de partida

```console
$ git log --oneline
9b7b479 commit tres
0d30164 commit dos
6717961 commit uno
```

## 2. una rama, por dentro

```console
$ ls .git/refs/heads
main

$ cat .git/refs/heads/main
9b7b479ff7a5c566d78cdd9f57dec1cf0612e351
```

## 3. crear una rama a mano

```console
$ git rev-parse HEAD > .git/refs/heads/experimento

$ git branch
  experimento
* main
```

## 4. dos ramas, un commit

```console
$ git rev-parse main experimento
9b7b479ff7a5c566d78cdd9f57dec1cf0612e351
9b7b479ff7a5c566d78cdd9f57dec1cf0612e351
```

## 5. la cabecera, por dentro

```console
$ cat .git/HEAD
ref: refs/heads/main
```

## 6. el estado desacoplado, en una línea

```console
$ git checkout 6717961
$ cat .git/HEAD
67179617156bf92840e8499af135328793f194e2
```

## 7. volver es reescribir el archivo

```console
$ git checkout main
$ cat .git/HEAD
ref: refs/heads/main
```

## 8. reset --soft

```console
$ git reset --soft HEAD~1
$ git log --oneline
0d30164 commit dos
6717961 commit uno
```

## 9. qué quedó después del suave

```console
$ git diff --cached --stat
 notas.txt | 1 +
 1 file changed, 1 insertion(+)

$ cat notas.txt
linea uno
linea dos
linea tres
```

## 10. reset --mixed · el que sale por defecto

```console
$ git reset --mixed HEAD~1
$ git diff --cached --stat
(nada)

$ cat notas.txt
linea uno
linea dos
linea tres
```

## 11. reset --hard

```console
$ git reset --hard HEAD~1
$ cat notas.txt
linea uno
linea dos
```

## 12. el commit que 'perdiste' sigue ahí

```console
$ git reset --hard HEAD@{1}
$ git log --oneline
9b7b479 commit tres
0d30164 commit dos
6717961 commit uno
```

## 13. las ramas empaquetadas

```console
$ git pack-refs --all
$ ls .git/refs/heads
(vacio)

$ cat .git/packed-refs
# pack-refs with: peeled fully-peeled sorted
9b7b479... refs/heads/experimento
9b7b479... refs/heads/main
```

## 14. cambiar de rama solo mueve el puntero

```console
$ git symbolic-ref HEAD
refs/heads/main

$ git switch rama-b
$ git symbolic-ref HEAD
refs/heads/rama-b
```

## 15. restore sí toca tu carpeta

```console
$ echo 'cambio local' >> notas.txt
$ git status --short
 M notas.txt

$ git restore notas.txt
$ git status --short
(sin salida: limpio)
```

## 16. las ramas de un clon

```console
$ git branch -a
* main
  remotes/origin/HEAD -> origin/main
  remotes/origin/main
```

## 17. y en un clon vienen empaquetadas

```console
$ find .git/refs/remotes -type f
.git/refs/remotes/origin/HEAD

$ cat .git/packed-refs
# pack-refs with: peeled fully-peeled sorted
0d30164... refs/remotes/origin/main
```

## 18. un commit de fusión tiene dos padres

```console
$ git cat-file -p HEAD
tree 5269af81936b3c57576341749aa795b9b826fa97
parent 0d30164008ba5f2b8facec34a5fa8a84414b0b82
parent 80c0bae3a1c84b0493c4d84f850580caade66580
```

## 19. el circunflejo elige el padre

```console
$ git log --oneline -1 HEAD^1
0d30164 commit dos

$ git log --oneline -1 HEAD^2
80c0bae commit en rama b
```

## 20. Git se niega, y hace bien

```console
$ git branch -d sin-fusionar
error: the branch 'sin-fusionar'
  is not fully merged
hint: If you are sure you want to delete it,
  run 'git branch -D sin-fusionar'
```

## 21. cada movimiento queda apuntado

```console
$ cat .git/logs/refs/heads/main
0000000000... 6717961... commit (initial)
6717961...    0d30164... commit
```
