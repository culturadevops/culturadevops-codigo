# Salida ejecutada — vídeo 222 «Para qué sirve Terraform y para qué NO»

> Corrida del 2026-09-08. El MISMO entorno (una red, un volumen, una base de datos, una caché y
> dos copias de la aplicación) levantado de dos formas: `a_mano.sh` con órdenes de Docker sueltas,
> y `tofu/main.tf` con OpenTofu oficial en contenedor (`ghcr.io/opentofu/opentofu:latest`) hablando
> con el Docker de la máquina. Reproducible con `bash demo.sh`.

---

## ⛔ La trampa que este banco evita a propósito

La comparación fácil es *«a mano hay que cambiar el nombre en quince sitios y con código es una
variable»*. **Es mentira**, y por eso no está en el vídeo: un guion de shell con una variable
también escala, y el `a_mano.sh` de al lado lo demuestra (`ENTORNO=produccion sh a_mano.sh`).
Quien monte su argumento ahí se lo tumban en los comentarios en diez minutos.

Lo que de verdad separa a las dos formas no es parametrizar. Es que **una lleva la cuenta de lo
que creó y la otra no**. Eso es lo que se mide.

---

## 1 · Levantar el entorno · 🥇 GANA A MANO

```
   a mano:      1522 ms
   con codigo:  5068 ms
```

**A mano es 3,3 veces más rápido**, y encima no hay que escribir un fichero de configuración ni
descargar un proveedor. Se dice en el vídeo tal cual: **para levantar algo una vez, escribir
código es peor**. Quien te venda lo contrario te está vendiendo algo.

## 2 · 🥇 Y AHORA LO EJECUTAS OTRA VEZ

```
   a mano:
     Error response from daemon: network with name pruebas-red already exists

   con codigo:
     No changes. Your infrastructure matches the configuration.
     Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
```

Aquí es donde se acaba el guion de shell: **no sabe que ya existe**. No es idempotente.

⚠️ Y hay que decirlo con precisión, porque en la primera versión de este banco puse una línea que
el número no demostraba: con `set -e`, como está escrito `a_mano.sh`, el guion muere en la primera
orden y **no crea nada a medias**. El problema no es que deje basura: es que **no puede converger**.
Sin `set -e` sería peor todavía, porque seguiría adelante creando lo que sí pueda. Ninguna de las
dos versiones sabe llegar al estado que le pides; solo sabe ejecutar órdenes.

## 3 · ¿Qué hay levantado?

```
   docker_container.app[0]      docker_image.app
   docker_container.app[1]      docker_image.postgres
   docker_container.cache       docker_image.redis
   docker_container.db          docker_network.red
                                docker_volume.datos

   piezas de las que lleva la cuenta: 9
```

A mano, la respuesta honesta es mirar `docker ps` y adivinar qué es de quién. Con código hay una
lista exacta de nueve piezas, y sabe cuáles son suyas.

## 4 · 🥇 Alguien toca por fuera (el martes, con prisa)

Se borra `pruebas-app-2` a mano, por detrás del código:

```
       # docker_container.app[1] will be created
     Plan: 1 to add, 0 to change, 0 to destroy.

   y lo repone solo:
     contenedores vivos tras el apply: 4
```

**El guion de shell no se habría enterado nunca de que faltaba uno.** Esto es lo que de verdad
compra la infraestructura como código: no velocidad, sino que alguien lleve la cuenta.

## 5 · 🥇 Destruir sin dejar basura

```
   a mano: lineas de borrado en a_mano.sh: 0
   con codigo: destruido en 6920 ms, sin escribir nada

     contenedores 'pruebas-' que quedan: 0
     redes 'pruebas-' que quedan:        0
     volumenes 'pruebas-' que quedan:    0
```

Para destruir a mano hay que escribir un **segundo** guion y mantenerlo en sintonía con el primero
para siempre. Y el que se olvida siempre es el volumen, que es justo el que cuesta dinero todos
los meses.

---

## El resumen que ordena el vídeo

| | a mano | con código |
|---|---|---|
| levantar una vez | **1.522 ms** ✅ | 5.068 ms |
| volver a ejecutarlo | revienta | «No changes» ✅ |
| ¿qué hay levantado? | adivina | 9 piezas, exactas ✅ |
| alguien borra algo | nadie se entera | lo detecta y lo repone ✅ |
| destruir | escribe otro guion | una orden, 0 restos ✅ |

**Terraform pierde la única fila que la gente mira y gana las cuatro que importan a los seis
meses.** Ese es el vídeo.
