# Salida ejecutada — vídeo 218 «Escribí Terraform en Python»

> Corrida del 2026-09-07 en `python:3.12-alpine`, solo biblioteca estándar.
> El «proveedor» son ficheros en un directorio: real, desechable y repetible sin cuenta ni tarjeta.

```
=== 1 · plan = deseado - actual ===
  no hay nada creado todavia:
  + crear     db.conf
  + crear     web.conf

  Plan: 2 a crear, 0 a cambiar, 0 a destruir.

=== 2 · apply ===
  + crear     db.conf
  + crear     web.conf

  Plan: 2 a crear, 0 a cambiar, 0 a destruir.

  Aplicado.
  lo que hay ahora en disco: db.conf web.conf 
  y el estado dice que son mios:
{
  "recursos": {
    "db.conf": {
      "gestionado": true
    },
    "web.conf": {
      "gestionado": true
    }
  }
}
=== 3 · plan otra vez, sin tocar nada ===
  (sin cambios)

  Plan: 0 a crear, 0 a cambiar, 0 a destruir.
  ^ idempotencia: la resta da cero. No es magia, es que deseado == actual.

=== 4 · cambio el deseado ===
  ~ cambiar   web.conf

  Plan: 0 a crear, 1 a cambiar, 0 a destruir.

############################################################
### 5 · Y AHORA LO IMPORTANTE:
###     ALGUIEN CREA UN RECURSO A MANO
############################################################
  alguien acaba de crear infra/otro-equipo.conf sin pasar por aqui.
  lo que hay ahora: db.conf otro-equipo.conf web.conf 

--- 5a · CON fichero de estado (lo correcto) ---
  ~ cambiar   web.conf

  Plan: 0 a crear, 1 a cambiar, 0 a destruir.
  ^ NO propone borrarlo. No esta en mi estado, asi que no es mio.

--- 5b · SIN fichero de estado (el modo peligroso) ---
  ~ cambiar   web.conf
  - DESTRUIR  otro-equipo.conf

  Plan: 0 a crear, 1 a cambiar, 1 a destruir.
  ^ PROPONE DESTRUIR EL FICHERO DE OTRO EQUIPO.
    Sin la lista de 'esto lo hice yo', 'lo que sobra' incluye lo que hizo otro.
```

### 🥇 Lo que sostiene el vídeo 218

**La tesis cabe en una resta:  `plan = deseado − actual`.** El lenguaje propio, los proveedores,
el grafo de dependencias y el bloqueo del estado son envoltorio alrededor de eso. El motor entero
de este juguete son tres listas: crear, cambiar, destruir.

**Y la idempotencia deja de ser magia:** aplicar dos veces no hace nada porque la resta da cero.

### 🔴 El momento del vídeo, demostrado

Alguien crea `infra/otro-equipo.conf` a mano, sin pasar por la herramienta. El mismo plan, con y
sin fichero de estado:

```
CON estado:   Plan: 0 a crear, 1 a cambiar, 0 a destruir
              ^ no lo toca. No está en mi estado, así que no es mío.

SIN estado:   - DESTRUIR  otro-equipo.conf
              Plan: 0 a crear, 1 a cambiar, 1 a destruir
              ^ propone borrar el fichero de otro equipo.
```

**Sin la lista de «esto lo hice yo», «lo que sobra» incluye lo que hizo otro.** El estado no es un
detalle de implementación ni un fichero molesto que hay que guardar en algún sitio: es lo ÚNICO
que autoriza a borrar. Se ve en una línea del código —de dónde sale el conjunto `mios`— y se
demuestra en dos corridas.
