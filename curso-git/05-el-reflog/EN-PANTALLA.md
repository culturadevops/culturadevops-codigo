# En Git no pierdes el trabajo: pierdes el nombre que llevaba a él — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. cinco pasos de trabajo

```console
$ git log --oneline
c9b3a2f paso 5
f511462 paso 4
67f900c paso 3
b07333e paso 2
3368883 paso 1
```

## 2. git reflog

```console
$ git reflog
c9b3a2f HEAD@{0}: commit: paso 5
f511462 HEAD@{1}: commit: paso 4
67f900c HEAD@{2}: commit: paso 3
b07333e HEAD@{3}: commit: paso 2
3368883 HEAD@{4}: commit (initial): paso 1
```

## 3. cada rama, su propio registro

```console
$ git reflog | wc -l
5

$ git reflog show otra
2454b9a otra@{0}: commit: commit en otra
73356cb otra@{1}: branch: Created from HEAD
```

## 4. dos commits menos

```console
$ git reset --hard HEAD~2
$ git log --oneline
67f900c paso 3
b07333e paso 2
3368883 paso 1
```

## 5. y el archivo, también

```console
$ cat obra.txt
trabajo 1
trabajo 2
trabajo 3
```

## 6. el reflog sí se acuerda

```console
$ git reflog
67f900c HEAD@{0}: reset: moving to HEAD~2
c9b3a2f HEAD@{1}: commit: paso 5
f511462 HEAD@{2}: commit: paso 4
```

## 7. volver es un solo comando

```console
$ git reset --hard HEAD@{1}
$ git log --oneline
c9b3a2f paso 5
f511462 paso 4
```

## 8. entero, y con el mismo hash

```console
$ cat obra.txt
trabajo 1
trabajo 2
trabajo 3
trabajo 4
trabajo 5
```

## 9. antes y después del rebase

```console
$ git log --oneline -1
62514cb arreglo

$ git rebase main
$ git log --oneline -1
6525749 arreglo
```

## 10. ORIG_HEAD lo tenía guardado

```console
$ cat .git/ORIG_HEAD
62514cbb78cb36dde799b28d17659334db8a8e9c
```

## 11. deshacer un rebase entero

```console
$ git reset --hard ORIG_HEAD
$ git log --oneline -1
62514cb arreglo
```

## 12. borrada sin preguntar

```console
$ git branch -D experimento-bueno
Deleted branch experimento-bueno (was e29a884).

$ git branch
  arreglo
* main
```

## 13. el commit sigue en el almacén

```console
$ git cat-file -t e29a884
commit
```

## 14. y el reflog también lo recuerda

```console
$ git reflog | grep experimento-bueno
c9b3a2f HEAD@{0}: checkout: moving from
  experimento-bueno to main
```

## 15. recuperar es reescribir el puntero

```console
$ git branch rescatada e29a884
$ git log --oneline -1 rescatada
e29a884 la idea buena

$ git show rescatada:idea.txt
la idea buena
```

## 16. corregir el último commit

```console
$ git log --oneline -1
c8769f5 mensaje correcto con trabajo dentro

$ git commit --amend -m 'mensaje nuevo'
$ git log --oneline -1
73356cb mensaje nuevo que pisa el anterior
```

## 17. el contenido original, intacto

```console
$ git cat-file -t c8769f5
commit

$ git show c8769f5:texto.txt
version buena
```

## 18. el reflog te dice qué pasó

```console
$ git reflog
73356cb HEAD@{0}: commit (amend): mensaje nuevo
c8769f5 HEAD@{1}: commit (initial): mensaje correcto
```

## 19. el cajón del trabajo a medias

```console
$ git stash
$ git stash list
stash@{0}: WIP on main: 73356cb mensaje nuevo
```

## 20. qué es un stash, de verdad

```console
$ git rev-parse refs/stash
aef997ff5fa44e931285dadcdeb7bdabf193274d

$ git cat-file -t aef997f
commit
```

## 21. un commit con dos padres

```console
$ git cat-file -p aef997f
tree 36d7b79411138a6787451fcb86e0...
parent 73356cb84cd23a36a4d671ef89c...
parent 226a147d140fdf2aace3e45de55...
```

## 22. tirar un stash por error

```console
$ git stash drop
Dropped refs/stash@{0} (aef997ff5fa...)

$ git stash list
(vacio)
```

## 23. recuperar un stash tirado

```console
$ git stash apply aef997f
On branch main
Changes not staged for commit:

$ cat texto.txt
algo distinto
trabajo a medias
```

## 24. un archivo que Git nunca vio

```console
$ git status --short borrador.txt
?? borrador.txt

$ rm borrador.txt
$ git log --all --oneline -- borrador.txt
(sin salida)
```

## 25. borrado y sacado del índice

```console
$ git add medio.txt
$ git rev-parse :medio.txt
8dad33f5f08dfc631a3c2f378ddee435c825b6b8

$ rm medio.txt
$ git reset
```

## 26. el contenido sigue ahí

```console
$ git cat-file -t 8dad33f
blob

$ git cat-file -p 8dad33f
medio hecho
```

## 27. lo que ya nadie nombra

```console
$ git fsck --lost-found
dangling blob 8dad33f5f08dfc631a3c2f...
dangling commit 652574999b309a663923...
```

## 28. preguntar, no recordar

```console
$ git config --get gc.reflogExpire
(sin definir: se usa el valor por defecto)

$ git config --get gc.reflogExpireUnreachable
(sin definir: se usa el valor por defecto)
```
