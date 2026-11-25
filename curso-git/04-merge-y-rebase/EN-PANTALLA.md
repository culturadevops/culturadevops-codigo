# Un conflicto de Git son tres entradas en el índice (no marcas en el archivo) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. el grafo antes de tocar nada

```console
$ git log --oneline --graph --all
* d559f94 cambio en main
| * fa98e74 cambio en A
|/
* 1c04fff base
```

## 2. el conflicto, tal cual sale

```console
$ git merge rama-a
Auto-merging doc.txt
CONFLICT (content): Merge conflict in doc.txt
Automatic merge failed; fix conflicts
  and then commit the result.
```

## 3. el mismo archivo, tres veces

```console
$ git ls-files --unmerged
100644 a3689d1cee64... 1  doc.txt
100644 31688a62e87e... 2  doc.txt
100644 e6f73ca95d99... 3  doc.txt
```

## 4. leer la base común

```console
$ git show :1:doc.txt
titulo
linea comun
pie
```

## 5. lo nuestro y lo suyo

```console
$ git show :2:doc.txt
titulo
version de MAIN
pie

$ git show :3:doc.txt
titulo
version de A
pie
```

## 6. Git te dice cuál es el antepasado

```console
$ git merge-base main rama-a
1c04fff42f9cadb5cf0652fc882651a9b133019f
```

## 7. y su contenido es la etapa 1

```console
$ git show 1c04fff:doc.txt
titulo
linea comun
pie
```

## 8. las marcas del disco

```console
$ cat doc.txt
titulo
<<<<<<< HEAD
version de MAIN
=======
version de A
>>>>>>> rama-a
pie
```

## 9. resolver es colapsar tres en una

```console
$ git ls-files --unmerged | wc -l
3

$ git add doc.txt
$ git ls-files --unmerged | wc -l
0
```

## 10. una entrada, etapa 0

```console
$ git ls-files --stage doc.txt
100644 21c0092045ef... 0  doc.txt
```

## 11. en medio del conflicto

```console
$ git ls-files --unmerged | wc -l
3

$ grep -c '<<<<<<<' doc.txt
1
```

## 12. y todo vuelve a su sitio

```console
$ git merge --abort
$ git ls-files --unmerged | wc -l
0

$ cat doc.txt
titulo
version de MAIN
pie
```

## 13. el commit de fusión

```console
$ git cat-file -p HEAD
tree ba738b7db7f69e5489018494...
parent d559f94a0125b01c9cb97e7b...
parent fa98e7424ce209e196d9b43...
author cultura devops <a@b.c> ...
```

## 14. la otra rama, intacta

```console
$ git rev-parse --short rama-a
fa98e74
```

## 15. el grafo después de fusionar

```console
$ git log --oneline --graph --all
*   7f93bd2 merge de rama-a resuelto
|\
| * fa98e74 cambio en A
* | d559f94 cambio en main
|/
* 1c04fff base
```

## 16. el hash antes del rebase

```console
$ git rev-parse HEAD
005dfc332e2c35f5df2865e1886bc28a0f66a4bf
```

## 17. y el hash después

```console
$ git rebase main
$ git rev-parse HEAD
28960534be300d2d6982e0a8b705990b793b33eb
```

## 18. el commit viejo sigue ahí

```console
$ git cat-file -t 005dfc3
commit

$ git log --oneline -1 005dfc3
005dfc3 cambio en A
```

## 19. fusionar sin divergencia

```console
$ git rev-list --all --count
2

$ git merge adelante
Updating 37d0c0c..564480c
Fast-forward
 f.txt | 1 +
```

## 20. Git te guarda el punto de partida

```console
$ cat .git/ORIG_HEAD
d559f94a0125b01c9cb97e7b0af549c3fc7e2daf
```
