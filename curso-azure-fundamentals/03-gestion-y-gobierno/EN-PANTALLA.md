# Azure Fundamentals 3: gobierno, costes y el examen AZ-900 — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. la jerarquía del bloque 2, otra vez

```console
/subscriptions/xxxx        <- aquí afecta a todo
  /resourceGroups/tienda   <- aquí, a esa carpeta
    /virtualMachines/web   <- aquí, a una máquina
```

## 2. de la documentación oficial

```console
tags: {
  "proyecto": "tienda",
  "entorno":  "pruebas",
  "dueño":    "equipo-web"
}
```

## 3. en mi máquina · lista pública de precios

```console
encendida siempre    35,04 USD/mes
solo en horario       8,45 USD/mes
el disco, apagada     0,61 USD/mes
```

## 4. de la página oficial de la certificación

```console
Nivel     Principiante
Producto  Azure
Rol       Administrador

Idiomas: inglés, japonés, chino,
coreano, ESPAÑOL, alemán, francés...
```
