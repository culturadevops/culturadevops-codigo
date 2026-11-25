# Laboratorio · curso «Monta un SOC en tu casa con Wazuh»

De aquí sale **todo** lo que el curso afirma. Ninguna cifra del guion puede venir de la
documentación de Wazuh: si no se midió aquí, no se dice.

```
docker compose up -d        levantar
docker compose down         parar (conserva los datos)
docker compose down -v      borrar del todo
```

| pieza | qué hace | dónde |
|---|---|---|
| `lab-wazuh-indexer` | guarda (fork de OpenSearch) | `:9200` |
| `lab-wazuh-manager` | decide: decoders, reglas, alertas | `:1514` eventos · `:1515` enrolar · `:8555`→55000 API (ver tropiezo 7) |
| `lab-wazuh-dashboard` | la cara — es lo que se graba | `:5601` |
| `lab-wazuh-victima` | Ubuntu con agente: **el objetivo de las demos** | — |

## ⛔ Regla de seguridad, sin excepciones

**Todo ataque va contra `lab-wazuh-victima`, y contra nada más.** Ni a la máquina anfitriona, ni
a la red de casa, ni a un servicio de internet «para el ejemplo». Un curso de detección se graba
atacando lo tuyo; lo demás no es una zona gris, es otra cosa.

Por eso la víctima es un contenedor del propio compose: existe para ser atacada, se borra con
`down -v` y no hay forma de confundirla con algo real.

## Lo medido el 2026-08-19

| | |
|---|---|
| versión | `WAZUH_VERSION="v4.9.2"` · revisión 40921 |
| indexer | 1,5 GiB |
| manager | 538,5 MiB |
| dashboard | 182,3 MiB |
| víctima | 420 KiB |
| **total** | **~2,2 GiB** |
| alertas de base | **752**, sin haber atacado nada |

⚠️ **Corrige lo que se dijo de memoria:** pide ~2,2 GB, no 6. Y por eso **sí** se puede renderizar
con el lab levantado: 2,2 de 31,5 no molesta.

## Los ocho tropiezos del montaje

Ninguno estaba previsto; salieron montándolo, y por eso valen para el curso.

1. **Sin certificados no arranca nada.** Hay que generarlos aparte
   (`docker compose -f generar-certificados.yml run --rm generador`). El dashboard muere con
   `ENOENT: dashboard-key.pem`.
2. **`plugins.security.disabled=true` por variable de entorno NO sirve** para saltárselo: el
   plugin de seguridad arranca igual.
3. **La imagen trae un `opensearch.yml` que apunta a `/etc/wazuh-indexer/certs/`, y esa carpeta
   no existe dentro de la imagen.** Montar ahí los certificados la crea, y entonces la política
   de Java deniega la lectura: `AccessControlException: access denied (...indexer.pem "read")`.
   Hay que dar un `opensearch.yml` propio apuntando a `/usr/share/wazuh-indexer/certs/`, que sí
   cae dentro de `path.home`.
4. **`apt install wazuh-agent` instala la ÚLTIMA** (4.14.7) y el manager la rechaza:
   `ERROR: Agent version must be lower or equal to manager version`. Hay que fijar la versión.
5. **La contraseña del indexer NO es la del compose** (descubierto el 2026-08-23). La imagen
   arranca con la de demostración, `admin:admin`, y el compose le dice al manager y al dashboard
   que usen `SecretPassword`. Resultado: `filebeat` muere en bucle con `401 Unauthorized` y **el
   indexer se queda vacío**.

   ⚠️ Y el fallo es **silencioso**, que es lo que lo hace bueno para el curso: el manager sigue
   escribiendo alertas en `/var/ossec/logs/alerts/alerts.json`, así que `agent_control` responde,
   las alertas se cuentan y todo parece correcto. Solo está vacío lo que se ve en el dashboard.
   El `MEDIDO.md` del 19 lo tenía delante —«el indexer todavía no responde»— y nadie lo miró.

   Se arregla poniéndole al indexer un `internal_users.yml` propio con el hash de la contraseña
   que sí se usa (`hash.sh -p SecretPassword`) y empujándolo al índice de seguridad con
   `securityadmin.sh`. El compose ya monta ese fichero.

6. **Un `ubuntu:24.04` pelado no tiene syslog ni SSH**, así que `/var/log/auth.log` no existe y
   el agente no tiene qué leer. Sin eso las lecciones 07 y 08 no tienen datos.

7. **En Windows, el puerto 55000 de la API del manager NO se puede publicar** (descubierto el
   2026-08-23). `docker compose up` deja el manager en `Created` y escupe:

   ```
   Error response from daemon: ports are not available: exposing port TCP 0.0.0.0:55000
   -> 127.0.0.1:0: listen tcp 0.0.0.0:55000: bind: Intento de acceso a un socket no
   permitido por sus permisos de acceso.
   ```

   No es un permiso ni un antivirus: Hyper-V/WinNAT se reserva rangos enteros de puertos altos
   y 55000 cae dentro de uno. Se ve con:

   ```
   netsh interface ipv4 show excludedportrange protocol=tcp
        54871       54970
        54971       55070     <- 55000 esta aqui dentro
        55071       55170
   ```

   ⚠️ Y los rangos **cambian en cada arranque de Windows**, así que el mismo compose que fue
   ayer puede fallar hoy. Por eso el arreglo no es «reserva tú el puerto» (`netsh ... add
   excludedportrange`, que pide administrador y reinicio) sino **publicarlo en otro**:
   `55500:55000`. Dentro del contenedor la API sigue en 55000, que es lo que espera Wazuh, y el
   dashboard ni se entera porque habla con el manager por la red de Docker.

   ✅ **CONFIRMADO el 2026-08-24, y el arreglo bueno es otro.** Windows se reinició y el 55500
   dejó de valer: el rango reservado se había movido a `55444-55543`. Y a la vez, el
   `54971-55070` que bloqueaba el 55000 el día 23 **ya no existía** — hoy el 55000 funcionaría.
   Buscar otro puerto alto es jugar a la lotería cada arranque.

   **El arreglo duradero es bajarse del rango dinámico**: Windows solo reserva de 49152 para
   arriba. El compose publica ahora la API en `8555:55000`, y ese no se lo puede quedar nadie.
   La tabla de arriba y la lección 02 se quedan como están: el 55500 fue un ejemplo real y su
   caducidad es justamente lo que la lección predice.

8. **El dashboard NUNCA había funcionado** (descubierto el 2026-08-23, y son tres fallos
   encadenados). El contenedor decía `Up`, el curso lo daba por bueno y el panel devolvía
   `503 Wazuh dashboard server is not ready yet` desde el día uno.

   a) **Buscaba el almacén dentro de sí mismo.** La imagen trae
      `opensearch.hosts: https://localhost:9200` y el log repetía cada dos segundos
      `[ConnectionError]: connect ECONNREFUSED 127.0.0.1:9200`. Las variables `INDEXER_URL` /
      `INDEXER_USERNAME` del compose **no las lee esta imagen**. Hay que montarle un
      `opensearch_dashboards.yml` propio apuntando a `https://wazuh.indexer:9200`.

   b) **`5601:5601` publicaba un puerto vacío.** Dentro escucha en el **443** — lo dice su
      propio `server.port`. El mapeo correcto es `5601:443`.

   c) **Y el bueno: `EACCES` al escribir su almacén de credenciales.**

      ```
      FATAL CLI ERROR Error: EACCES: permission denied, open
      '/etc/wazuh-dashboard/opensearch_dashboards.keystore'
      ```

      Los scripts de la imagen fijan `OSD_PATH_CONF=/etc/wazuh-dashboard`, pero **esa carpeta
      no existe en la imagen**: la crea Docker al montar ahí los certificados, y Docker crea
      las carpetas que le faltan **como root**. El contenedor corre como `uid=1000`, así que
      no puede escribir dentro. Sin keystore no hay usuario ni contraseña, el proceso ni
      siquiera puede preguntar la versión del indexer —`Unable to retrieve version information
      from OpenSearch nodes`— y se queda migrando para siempre.

      Se arregla poniendo `opensearch.username` y `opensearch.password` **en el yml** en vez de
      esperar al keystore. El `EACCES` sigue saliendo en el log y ya da igual.

   ⚠️ La lección de método está en (c) y vale para cualquier contenedor: **una ruta que te
   inventas en un `volumes:` se convierte en una carpeta de root**, y un contenedor que no
   corre como root no puede escribir en ella.

Y uno de método, para quien repita el montaje: al añadir el `<localfile>` con `sed` sustituyendo
`</ossec_config>`, **se inserta dos veces** — `ossec.conf` tiene varios cierres de bloque.

## La demo de la lección 08, ya comprobada

10 intentos de SSH contra `lab-wazuh-victima` con un usuario inexistente:

```
regla 5710  nivel  5  x19   sshd: usuario inexistente     MITRE T1110.001
regla 5503  nivel  5  x9    PAM: login fallido            MITRE T1110.001
regla 5551  nivel 10  x1    PAM: multiples fallos         MITRE T1110
regla 5712  nivel 10  x1    sshd: BRUTE FORCE             MITRE T1110
```

28 de ruido y 1 que importa. El mapeo MITRE viene de fábrica, sin configurar nada.

## Corrección al temario

- **`vm.max_map_count` ya vale 262144** en la VM de WSL de Docker Desktop. El fallo clásico de
  arranque **no ocurre aquí**, así que la lección 02 no lo enseña fallando: lo explica y enseña
  el valor real. No se finge un error — y además ahora hay cinco fallos de verdad que enseñar.

## Seguridad del propio lab

Contraseñas de ejemplo a la vista en el compose, y certificados autofirmados generados en local.
Es un laboratorio desechable: se borra con `down -v` y no guarda nada que importe.

*(La versión inicial de este documento decía que se desactivaba la seguridad del indexer con
`plugins.security.disabled=true`. **No se puede**: se probó y el plugin arranca igual. Por eso el
lab lleva certificados de verdad — ver el tropiezo 2.)*

⛔ **Eso mismo en una máquina de verdad es una barbaridad**, y el curso lo dice en voz alta cuando
toque. Un lab que no avisa de en qué se diferencia de producción enseña a montar producción mal.
