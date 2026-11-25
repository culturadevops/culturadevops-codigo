# Por qué limpiar un repositorio de Git puede dejarlo MÁS grande — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. el repositorio real

```console
$ git count-objects -vH
count: 0
in-pack: 3206
packs: 1
size-pack: 68.56 MiB
```

## 2. los dos archivos del paquete

```console
$ ls -la .git/objects/pack/
    90840  pack-79d42acb....idx
 71797034  pack-79d42acb....pack
```

## 3. una línea por objeto

```console
$ git verify-pack -v pack-79d42acb....idx
28dda8c8... commit 265 181 12
9066dcb2... commit 1175 900 193
3ee85482... commit 402 257 1093
fdd6457f... commit 2360 1297 1350
```

## 4. qué hay dentro, por tipo

```console
$ git verify-pack -v ... | awk '{print $2}' | uniq -c
   1996 blob
   1043 tree
    167 commit
```

## 5. cuántos objetos en cada nivel

```console
$ git verify-pack -v ... | awk '{print $6}' | uniq -c
   2011 nivel 0
    485 nivel 1
    256 nivel 2
    162 nivel 3
     97 nivel 4
     54 nivel 5
```

## 6. hasta dónde llegan las cadenas

```console
$ git verify-pack -v ... | grep 'chain length' | tail -5
chain length = 18: 2 objects
chain length = 19: 2 objects
chain length = 20: 3 objects
chain length = 21: 5 objects
chain length = 22: 5 objects
```

## 7. 40 versiones de un archivo de texto

```console
$ git count-objects -v
count: 120

$ du -sk .git
452
```

## 8. después de empaquetar

```console
$ git gc
$ git count-objects -vH
count: 0
in-pack: 120
size-pack: 31.86 KiB

$ du -sk .git
154
```

## 9. la cuenta que importa

```console
$ ... | awk '{s+=$3} END {print s}'
212211

$ ... | awk '{s+=$4} END {print s}'
20580
```

## 10. 5 versiones de un binario

```console
$ git verify-pack -v ... | grep blob
832b6da... 400000 400135
bf699ef... 400000 400135
b0699e7... 400000 400135
5676361... 400000 400135
8cc4f52... 400000 400135
```

## 11. los 3 mayores del repo real

```console
$ git verify-pack -v ... | sort -k4 -rn | head -3
12f46d90... blob 20792681 20738932
3e26e619... blob 20897137 20690175
539b8e90... blob 16701555 16703567
```

## 12. el punto de partida, al byte

```console
$ find .git -type f -printf '%s\n' \
$   | awk '{s+=$1} END {print s}'
74860
```

## 13. y ahora limpiamos

```console
$ git gc --aggressive --prune=now
$ find .git -type f -printf '%s\n' \
$   | awk '{s+=$1} END {print s}'
76077
```

## 14. reempaquetar un repo ya óptimo

```console
$ du -sk .git
154

$ git repack -a -d --write-bitmap-index
$ git commit-graph write --reachable
$ du -sk .git
162
```

## 15. dónde se fueron los 8 kilos

```console
$ ls -la .git/objects/pack/*.bitmap
2244 bytes

$ ls -la .git/objects/info/commit-graph
3512 bytes
```

## 16. el repo real no los tiene

```console
$ ls .git/objects/pack/*.bitmap
(sin bitmap)

$ ls .git/objects/info/commit-graph
(sin commit-graph)
```

## 17. preguntar, nunca recordar

```console
$ git config --get pack.window
(sin definir: por defecto 10)

$ git config --get pack.depth
(sin definir: por defecto 50)
```

## 18. una ventana 25 veces mayor

```console
$ git repack -a -d -f --window=250 --depth=50

$ ls -la .git/objects/pack/*.pack
29209 bytes  (antes: 29209 bytes)
```

## 19. el umbral de los archivos grandes

```console
$ git config --get core.bigFileThreshold
(sin definir: por defecto 512m)
```

## 20. lo que Git haría solo

```console
$ git config --get maintenance.auto
(sin definir)

$ # git maintenance start
```
