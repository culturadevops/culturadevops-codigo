# SALIDA extra — Google Cloud en local (vídeo 411)

Generado 2026-10-13 22:06 UTC con `python correr_extra.py`.

## 1 · Un mensaje, dos suscripciones

### un tema, dos suscripciones

`$ curl …/topics/altas/subscriptions`

```
"subscriptions": ["projects/demo/subscriptions/envios-altas", "projects/demo/subscriptions/facturacion-altas"]
```

### publicar UN mensaje

`$ curl -X POST …/topics/altas:publish`

```
{
  "messageIds": ["3"]
}
```

### lo que recibe facturacion-altas

`$ curl -X POST …/subscriptions/facturacion-altas:pull`

```
pedido 2001
```

### lo que recibe envios-altas

`$ curl -X POST …/subscriptions/envios-altas:pull`

```
pedido 2001
```

## 2 · Firestore: una consulta

### cuántos clientes hay

`$ curl …/documents/clientes | grep -c nombre`

```
4
```

### clientes con más de 2 pedidos

`$ curl -X POST …/documents:runQuery  (where pedidos > 2)`

```
Ana: 3 pedidos
Marta: 5 pedidos
```
