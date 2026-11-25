# SALIDA extra 2 — colas en Azurite (vídeo 409)

Generado 2026-10-13 21:04 UTC con `python correr_extra2.py`.

### crear la cola

`$ az storage queue create -n pedidos …`

```
{
  "created": true
}
```
(código de salida 0)

### meter dos mensajes

`$ az storage message put -q pedidos --content … (x2)`

```
dos mensajes
```
(código de salida 0)

### mirar sin sacar

`$ az storage message peek -q pedidos --num-messages 5 …`

```
pedido 1001
pedido 1002
```
(código de salida 0)

### un trabajador saca uno (invisible 30 s)

`$ az storage message get -q pedidos --visibility-timeout 30 …`

```
contenido: pedido 1001
veces sacado: 1
```

### lo que ven los demás mientras tanto

`$ az storage message peek -q pedidos --num-messages 5 …`

```
pedido 1002
```
(código de salida 0)

### terminado: lo borra

`$ az storage message delete --id … --pop-receipt …`

```
borrado
```
(código de salida 0)

### cuántos quedan

`$ az storage queue metadata show / peek …`

```
pedido 1002
```
(código de salida 0)
