# SALIDA — k9s (vídeo 332)

Generado 2026-10-07 22:21 UTC con `python correr.py`. k3s en Docker, k9s v0.51.0, kubectl v1.37.1, ttyd 1.7.7.

### las cargas

`$ kubectl get pods -n tienda`

```
NAME                     READY   STATUS    RESTARTS      AGE
pagos-854db45ff8-chdw7   0/1     Error     2 (20s ago)   36s
web-68b64b4b66-4wpzw     1/1     Running   0             36s
web-68b64b4b66-lwb62     1/1     Running   0             36s
web-68b64b4b66-txxr8     1/1     Running   0             36s
```

## 1 · k9s en una terminal web

### versiones

`$ k9s version -s; kubectl version --client`

```
Version              v0.51.0
Commit               558caafe7ba067467de46b320cc22ef11fef9c34
Date                 2026-06-06T14:04:25Z
Client Version: v1.37.1
```

### capturas

`$ node teclear.js`

```
ok 01-pods
ok 02-deploy
ok 03-filtro-pagos
ok 04-logs-pagos
ok 05-logs-previos
ok 06-describe
ok 07-shell
ok 08-confirmar-borrar
ok 08a-ok
ok 08b-recreado
ok 10-escalar
ok 11-escalado
ok 12-xray
ok 09-readonly
```

## 2 · Lo que se hizo desde k9s, comprobado con kubectl

### pods después de borrar uno con ctrl-d

`$ kubectl get pods -n tienda -l app=web`

```
NAME                   READY   STATUS    RESTARTS   AGE
web-68b64b4b66-6l6pk   1/1     Running   0          16s
web-68b64b4b66-jhvw6   1/1     Running   0          36s
web-68b64b4b66-lwb62   1/1     Running   0          2m3s
web-68b64b4b66-sn56p   1/1     Running   0          16s
web-68b64b4b66-txxr8   1/1     Running   0          2m3s
```

### réplicas después de escalar desde k9s

`$ kubectl get deploy -n tienda`

```
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
pagos   0/1     1            0           2m8s
web     5/5     5            5           2m8s
```

### logs del que falla

`$ kubectl logs -n tienda deploy/pagos --previous`

```
conectando a la base de datos...
ERROR: no encuentro DB_PASSWORD
```

### eventos

`$ kubectl get events -n tienda --field-selector reason=Killing`

```
LAST SEEN   TYPE     REASON    OBJECT                     MESSAGE
37s         Normal   Killing   pod/web-68b64b4b66-4wpzw   Stopping container nginx
```

### modo solo lectura

`$ k9s --readonly (¿deja borrar?)`

```
ver captura 09-readonly
```
