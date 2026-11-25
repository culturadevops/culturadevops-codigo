# Medido en el laboratorio · 2026-08-23 20:25 UTC

⚠️ Generado por `medir.py`. **No editar a mano**: si un número de aquí no cuadra, se
vuelve a medir. Es la única fuente de cifras del curso.

## Contenedores

- `lab-wazuh-dashboard` · Up 15 seconds · imagen `wazuh/wazuh-dashboard:4.9.2`
- `lab-wazuh-manager` · Up 2 minutes · imagen `wazuh/wazuh-manager:4.9.2`
- `lab-wazuh-victima` · Up 2 minutes · imagen `ubuntu:24.04`
- `lab-wazuh-indexer` · Up 2 minutes · imagen `wazuh/wazuh-indexer:4.9.2`

## RAM y CPU (foto puntual)

| contenedor | RAM | % | CPU |
|---|---|---|---|
| `lab-wazuh-dashboard` | 163.7MiB / 15.36GiB | 1.04% | 2.50% |
| `lab-wazuh-manager` | 579.2MiB / 15.36GiB | 3.68% | 12.40% |
| `lab-wazuh-victima` | 1.527MiB / 15.36GiB | 0.01% | 0.00% |
| `lab-wazuh-indexer` | 1.734GiB / 15.36GiB | 11.29% | 2.47% |

## Versión que dice el manager

```
WAZUH_VERSION="v4.9.2"
WAZUH_REVISION="40921"
WAZUH_TYPE="server"
```

## Agentes

```
Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh.manager (server), IP: 127.0.0.1, Active/Local
   ID: 001, Name: victima, IP: any, Never connected

List of agentless devices:
```

## Índices y lo que ocupan

```
index                        docs.count store.size
.plugins-ml-config                    1      3.9kb
.opensearch-observability             0       208b
security-auditlog-2026.08.19        204     44.7kb
security-auditlog-2026.08.23        257    335.6kb
wazuh-monitoring-2026.34w             4     32.7kb
wazuh-alerts-4.x-2026.08.23        5265      9.5mb
.kibana_1                             0       208b
.opendistro_security                 10     78.6kb
wazuh-statistics-2026.34w             2     24.1kb
```

## Alertas acumuladas hasta ahora: **1313**

Sin haber atacado nada. Es la línea base del ruido, y es el dato de la lección 05.

## Lo que ocupan las imágenes

```
wazuh/wazuh-dashboard:4.9.2	1.79GB
wazuh/wazuh-indexer:4.9.2	4.23GB
wazuh/wazuh-manager:4.9.2	2GB
wazuh/wazuh-certs-generator:0.0.2	218MB
```
