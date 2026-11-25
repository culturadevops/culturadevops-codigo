# SALIDA — curso «De cero a producción»

> Generado por `paso_a_paso.py`. **No se escribe a mano.**

```
de cero a producción · 2026-10-05 18:23:56Z · OpenTofu v1.12.5 · Docker 29.6.2

== Paso 1 · El repositorio: el secreto que se queda en la historia ==
   (a fondo: Git por dentro (17-23))
  git add . && git commit   -> se cuela el .env
  git rm .env && git commit -> «arreglado»
  git ls-files: tienda.py
  git log -S <la clave>:
    48b11ff quito el .env
    d612a29 primera versión de la tienda
  git show <primer commit>:.env -> DB_PASSWORD=clave-de-produccion-9f3
  lo correcto: .gitignore ANTES del primer commit, y si ya se coló, la clave se cambia: está filtrada

== Paso 2 · La imagen: grande y como root, o pequeña y sin privilegios ==
   (a fondo: Contenedores por dentro (128))
  Dockerfile.ingenuo       421 MB · corre como root uid=0
  Dockerfile                52 MB · corre como tienda uid=10001

== Paso 3 · La infraestructura con OpenTofu, y el estado que guarda la clave ==
   (a fondo: OpenTofu desde cero (126))
  sin cifrar: Apply complete! Resources: 7 added, 0 changed, 0 destroyed.
  la clave, en claro en terraform.tfstate: 1 vez (y la variable es «sensitive»)
  con el estado cifrado: Apply complete! Resources: 7 added, 0 changed, 0 destroyed.
  la clave en terraform.tfstate: 0 veces · empieza por: o7/qnElbpHgqepmaiWtQLVFF...
  tofu plan con otra frase: código 1 · Error message: failed to write backup file: decryption failed for all

== Paso 4 · Los secretos: lo que enseña docker inspect ==
   (a fondo: Terraform 2026: variables y secretos (253))
  como variable de entorno:  POSTGRES_PASSWORD=clave-de-produccion-9f3
  como fichero (producción): POSTGRES_PASSWORD_FILE=/run/secrets/clave_db

== Paso 5 · La red y el certificado: diagnostico.sh, de abajo arriba ==
   (a fondo: Redes para gente de DevOps (314))
  la tienda tal cual salió del curso de incidentes:
  diagnóstico de http://capstone-tienda-vieja:8000/salud
    DNS     ✓ capstone-tienda-vieja -> 192.168.16.7 (2 ms)
    TCP     ✓ 192.168.16.7:8000 abierto (2 ms)
    HTTP    ✗ contesta 501
    -> falla la capa 4 (HTTP)
  -> le faltaba do_HEAD (BaseHTTPRequestHandler contesta 501). Añadido, y la de producción:
  diagnóstico de https://tienda.prod.test/salud
    DNS     ✓ tienda.prod.test -> 192.168.16.6 (2 ms)
    TCP     ✓ 192.168.16.6:443 abierto (2 ms)
    TLS     ✓ verificado · DNS:tienda.prod.test · 1 certificados en la cadena · caduca en 89 días
    HTTP    ✓ 200 en 0.005750 s
    CUERPO  ✓ 12 bytes en 0.005830 s
    -> todo bien (0)
  código de salida 0

== Paso 6 · Las alertas: que Prometheus vea las dos réplicas ==
   (a fondo: Observabilidad de verdad (41-60) · Incidentes (315))
  objetivo capstone-tienda-a:8000   up
  objetivo capstone-tienda-b:8000   up
  alertas cargadas: ErroresAltos, TiendaCaida

== Paso 7 · La copia de seguridad, probada: ensayo.sh contra producción ==
   (a fondo: Restaurar, no copiar (313))
  ensayo de restauración · base de datos «tienda» · 2026-10-05 18:24:37Z
    1 · copia: 32 KB · 1 tablas en la huella
    2 · restaurada en un servidor nuevo en 95 ms
    3 · verificación, tabla por tabla:
        pedidos          5000 filas  ✓
    4 · RTO medido: 95 ms · RPO: lo escrito en los últimos 1 s (la edad de la copia)
    RESULTADO: la copia sirve (código 0)
  código de salida 0

== Paso 8 · Desplegar sin cortar: réplica a réplica, con tráfico ==
   (a fondo: Un incidente de principio a fin (315))
  tofu apply -replace=tienda["a"]: Apply complete! Resources: 1 added, 0 changed, 1 destroyed. (4 s)
  tofu apply -replace=tienda["b"]: Apply complete! Resources: 1 added, 0 changed, 1 destroyed. (4 s)
  pagos durante el despliegue: 200: 174

== Paso 9 · ¿Listo para producción? La lista, comprobada ==
   (a fondo: todos)
  ✓ .env fuera del repositorio (.gitignore)
  ✓ la imagen no corre como root
  ✓ el estado de OpenTofu, cifrado
  ✓ ninguna clave en docker inspect
  ✓ diagnóstico de red y TLS: código 0
  ✓ al certificado le quedan más de 30 días
  ✓ alertas cargadas y réplicas vigiladas
  ✓ la copia se restaura: ensayo.sh, código 0
  ✓ desplegar sin cortar: 0 pagos fallidos
  RESULTADO: 9 de 9 · listo para producción (código 0)
```
