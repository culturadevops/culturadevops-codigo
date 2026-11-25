# Docker decía «Up» cuatro días y el panel no funcionaba (Wazuh en Docker) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. sin este paso no arranca nada

```console
$ docker compose up -d

lab-wazuh-dashboard exited with code 1
Error: ENOENT: no such file or directory,
  open '/etc/wazuh-dashboard/certs/dashboard-key.pem'

$ docker compose -f generar-certificados.yml run --rm generador
```

## 2. comprobarlo, no suponerlo

```console
$ wsl -d docker-desktop sysctl vm.max_map_count
vm.max_map_count = 262144

$ docker run --rm alpine cat /proc/sys/vm/max_map_count
262144
```

## 3. el manager se queda en «Created»

```console
$ docker compose up -d

Container lab-wazuh-manager   Starting
Error response from daemon: ports are not available:
  listen tcp 0.0.0.0:55000: bind: Intento de acceso a un
  socket no permitido por sus permisos de acceso.

```

## 4. quién se lo ha quedado

```console
> netsh interface ipv4 show excludedportrange protocol=tcp

Puerto de inicio    Puerto final
     54871       54970
     54971       55070      <- el 55000 esta aqui
     55071       55170
```

## 5. lo que decía cada uno

```console
$ docker ps --format '{{.Names}}\t{{.Status}}'
lab-wazuh-dashboard   Up 4 hours

$ curl -sk https://localhost:5601/app/login
Wazuh dashboard server is not ready yet
HTTP 503
```

## 6. la primera línea del registro, y nadie la leyó

```console
$ docker logs lab-wazuh-dashboard | head -2

FATAL CLI ERROR Error: EACCES: permission denied, open
  '/etc/wazuh-dashboard/opensearch_dashboards.keystore'

Unable to retrieve version information from OpenSearch nodes.
```

## 7. arranque en frío, cronometrado

```console
docker dice Started            1 s
el indexer contesta            8 s
el manager contesta            8 s
el dashboard sirve la pagina   13 s
se abre desde el navegador     13 s
```

## 8. RAM real, con el laboratorio en marcha

```console
$ docker stats --no-stream

lab-wazuh-indexer     1.734GiB
lab-wazuh-manager     579.2MiB
lab-wazuh-dashboard   163.7MiB
lab-wazuh-victima     1.5MiB
```

## 9. las tres preguntas

```console
$ docker exec lab-wazuh-indexer curl -sk -u admin:*** \
  https://localhost:9200/_cluster/health

$ docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l

$ curl -sk -o /dev/null -w '%{http_code}' https://localhost:5601/app/login
200
```
