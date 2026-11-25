# Salida ejecutada — vídeo 225 «Por qué tu repo de Git engorda»

> Corrida del 2026-09-08 en `alpine/git:latest`, desde un repositorio vacío.
> Reproducible con `docker run --rm --entrypoint sh -v "$PWD:/w" alpine/git:latest /w/demo.sh`.

---

## 1 · Un repositorio normal, solo código

40 ficheros de Go, un commit:

```
   .git pesa: 476.0K
   count: 42   size: 168.00 KiB   in-pack: 0
```

Medio mega. Un repositorio de código, por muchos años que tenga, no crece así.

## 2 · Alguien sube un binario de 20 MB

```
   .git pesa: 19.6M
```

## 3 · 🥇 LO BORRA, Y HACE 20 COMMITS MÁS

```
   el fichero ya NO esta en el proyecto:
     (no existe, borrado hace 20 commits)

   y sin embargo .git pesa: 20.0M
```

**Subió.** Después de borrarlo. Porque Git no guarda la foto de hoy: guarda la historia entera, y
ese objeto tiene que seguir ahí para poder volver a cualquier commit anterior. Borrar un fichero
es un commit más, no una marcha atrás.

## 4 · 🥇 Y AHORA `git gc`, QUE ES DONDE SALTA LA SORPRESA

```
   antes:    count: 106   size: 19.49 MiB   in-pack: 0
   despues:  count: 0     size: 0 bytes     in-pack: 106   size-pack: 19.09 MiB

   .git pesa ahora: 19.3M
```

Los 106 objetos sueltos se juntan en **un** paquete y se comprimen unos contra otros. Y aun así,
de 20,0 a 19,3 M: **`git gc` no arregla esto**. Es el consejo que da todo el mundo y no sirve para
lo que la gente cree que sirve.

⚠️ Con honestidad sobre la prueba: el binario de aquí son bytes aleatorios, que es lo peor posible
para comprimir. Un instalador o un `.zip` de verdad se comportan igual (ya vienen comprimidos).
Un fichero grande de TEXTO —un CSV, un volcado, un registro— sí encogería bastante con `gc`. El
vídeo lo dice.

## 5 · La pregunta que casi nadie sabe hacer

```
$ git verify-pack -v .git/objects/pack/*.idx | sort -k3 -n -r | head

     22be8ee245f4  tipo=blob     20000000 bytes
     fd4bffb4f3d6  tipo=tree         1388 bytes
     55b4e051af5e  tipo=blob          290 bytes

   y a qué fichero corresponde: gordo.bin
```

Veinte millones de bytes contra mil trescientos del siguiente. **Esa es la orden que contesta «¿qué
es lo que ocupa?»**, y el segundo paso —cruzarlo con `git rev-list --objects --all`— es el que le
pone nombre al culpable.

## 6 · 🥇 QUITARLO DE VERDAD, Y LO QUE CUESTA

```
   el commit actual es:     a6b043af2174
   .git pesa ahora:         168.0K
   y el commit actual es:   700651502b93

   ⛔ HA CAMBIADO.
```

De 20 M a **168 K**. Funciona. Pero mira las otras dos líneas: el identificador del commit es
otro. Y con él, **todos** los commits desde el que se tocó, porque cada uno incluye el del
anterior. Cualquiera que tenga una copia del repositorio se queda con una historia que ya no
existe.

Ese es el precio, y es el motivo real por el que casi nadie limpia su repositorio: no es difícil,
es que hay que avisar a todo el mundo y que todos vuelvan a clonar.

---

## El resumen que ordena el vídeo

| paso | .git |
|---|---|
| solo código | 476 K |
| se sube un binario de 20 MB | 19,6 M |
| **se borra el binario + 20 commits** | **20,0 M** ⬆ |
| `git gc --aggressive` | 19,3 M |
| se reescribe la historia | **168 K** |
