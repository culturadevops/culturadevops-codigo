# SALIDA — CrowdSec (vídeo 327)

Generado 2026-10-07 21:15 UTC con `python correr.py`. Imágenes crowdsecurity/crowdsec:latest y crowdsecurity/openresty:latest.

## 1 · Levantar el laboratorio

### arranque de crowdsec

`$ docker run -d --name crowdsec ... crowdsecurity/crowdsec`

```
listo en 15 s
version: v1.8.1-909b5157
```

## 2 · Lo que lee y lo que sabe detectar

### versión

`$ cscli version`

```
version: v1.8.1-909b5157
Codename: alphaga
BuildDate: 2026-09-03_11:03:45
GoVersion: 1.26.8
Platform: docker
libre2: C++
User-Agent: crowdsec/v1.8.1-909b5157-docker
Constraint_parser: >= 1.0, <= 3.0
Constraint_scenario: >= 1.0, <= 3.0
Constraint_api: v1
Constraint_acquis: >= 1.0, < 2.0
Built-in optional components: cscli_setup, datasource_appsec, datasource_cloudwatch, datasource_docker, datasource_file, datasource_http, datasource_journalctl, datasource_k8s-audit, datasource_kafka, datasource_kinesis, datasource_kubernetes, datasource_loki, datasource_s3, datasource_syslog, datasource_victorialogs, datasource_wineventlog, db_mysql, db_postgres, db_sqlite
```

### colecciones

`$ cscli collections list`

```
----------------------------------------------------------------------------------------------------------------
 COLLECTIONS                                                                                                    
----------------------------------------------------------------------------------------------------------------
 Name                                 📦 Status   Version  Local Path                                           
----------------------------------------------------------------------------------------------------------------
 crowdsecurity/base-http-scenarios    ✔️  enabled  1.4      /etc/crowdsec/collections/base-http-scenarios.yaml   
 crowdsecurity/http-cve               ✔️  enabled  3.0      /etc/crowdsec/collections/http-cve.yaml              
 crowdsecurity/linux                  ✔️  enabled  0.4      /etc/crowdsec/collections/linux.yaml                 
 crowdsecurity/nginx                  ✔️  enabled  0.3      /etc/crowdsec/collections/nginx.yaml                 
 crowdsecurity/sshd                   ✔️  enabled  0.9      /etc/crowdsec/collections/sshd.yaml                  
 crowdsecurity/whitelist-good-actors  ✔️  enabled  0.4      /etc/crowdsec/collections/whitelist-good-actors.yaml 
----------------------------------------------------------------------------------------------------------------
```

### escenarios

`$ cscli scenarios list`

```
----------------------------------------------------------------------------------------------------------------------------------------
 SCENARIOS                                                                                                                              
----------------------------------------------------------------------------------------------------------------------------------------
 Name                                              📦 Status   Version  Local Path                                                      
----------------------------------------------------------------------------------------------------------------------------------------
 crowdsecurity/apache_log4j2_cve-2021-44228        ✔️  enabled  0.7      /etc/crowdsec/scenarios/apache_log4j2_cve-2021-44228.yaml       
 crowdsecurity/CVE-2017-9841                       ✔️  enabled  0.2      /etc/crowdsec/scenarios/CVE-2017-9841.yaml                      
 crowdsecurity/CVE-2019-18935                      ✔️  enabled  0.2      /etc/crowdsec/scenarios/CVE-2019-18935.yaml                     
 crowdsecurity/CVE-2022-26134                      ✔️  enabled  0.4      /etc/crowdsec/scenarios/CVE-2022-26134.yaml                     
 crowdsecurity/CVE-2022-35914                      ✔️  enabled  0.2      /etc/crowdsec/scenarios/CVE-2022-35914.yaml                     
 crowdsecurity/CVE-2022-37042                      ✔️  enabled  0.2      /etc/crowdsec/scenarios/CVE-2022-37042.yaml                     
 crowdsecurity/CVE-2022-40684                      ✔️  enabled  0.3      /etc/crowdsec/scenarios/CVE-2022-40684.yaml                     
 crowdsecurity/CVE-2022-41082                      ✔️  enabled  0.4      /etc/crowdsec/scenarios/CVE-2022-41082.yaml                     
 crowdsecurity/CVE-2022-41697                      ✔️  enabled  0.2      /etc/crowdsec/scenarios/CVE-2022-41697.yaml                     
 crowdsecurity/CVE-2022-42889                      ✔️  enabled  0.3      /etc/crowdsec/scenarios/CVE-2022-42889.yaml                     
 crowdsecurity/CVE-2022-44877                      ✔️  enabled  0.4      /etc/crowdsec/scenarios/CVE-2022-44877.yaml                     
 crowdsecurity/CVE-2022-46169                      ✔️  enabled  0.2      /etc/crowdsec/scenarios/CVE-2022-46169.yaml                     
 crowdsecurity/CVE-2023-22515                      ✔️  enabled  0.1      /etc/crowdsec/scenarios/CVE-2023-22515.yaml                     
 crowdsecurity/CVE-2023-22518                      ✔️  enabled  0.3      /etc/crowdsec/scenarios/CVE-2023-22518.yaml                     
 crowdsecurity/CVE-2023-49103                      ✔️  enabled  0.3      /etc/crowdsec/scenarios/CVE-2023-49103.yaml                     
 crowdsecurity/CVE-2024-0012                       ✔️  enabled  0.1      /etc/crowdsec/scenarios/CVE-2024-0012.yaml                      
 crowdsecurity/CVE-2024-38475                      ✔️  enabled  0.1      /etc/crowdsec/scenarios/CVE-2024-38475.yaml                     
 crowdsecurity/CVE-2024-9474                       ✔️  enabled  0.1      /etc/crowdsec/scenarios/CVE-2024-9474.yaml                      
 crowdsecurity/f5-big-ip-cve-2020-5902             ✔️  enabled  0.3      /etc/crowdsec/scenarios/f5-big-ip-cve-2020-5902.yaml            
 crowdsecurity/fortinet-cve-2018-13379             ✔️  enabled  0.4      /etc/crowdsec/scenarios/fortinet-cve-2018-13379.yaml            
 crowdsecurity/grafana-cve-2021-43798              ✔️  enabled  0.3      /etc/crowdsec/scenarios/grafana-cve-2021-43798.yaml             
 crowdsecurity/http-admin-interface-probing        ✔️  enabled  0.5      /etc/crowdsec/scenarios/http-admin-interface-probing.yaml       
 crowdsecurity/http-backdoors-attempts             ✔️  enabled  0.6      /etc/crowdsec/scenarios/http-backdoors-attempts.yaml            
 crowdsecurity/http-bad-user-agent                 ✔️  enabled  1.2      /etc/crowdsec/scenarios/http-bad-user-agent.yaml                
 crowdsecurity/http-crawl-non_statics              ✔️  enabled  0.7      /etc/crowdsec/scenarios/http-crawl-non_statics.yaml             
 crowdsecurity/http-cve-2021-41773                 ✔️  enabled  0.3      /etc/crowdsec/scenarios/http-cve-2021-41773.yaml                
 crowdsecurity/http-cve-2021-42013                 ✔️  enabled  0.3      /etc/crowdsec/scenarios/http-cve-2021-42013.yaml                
 crowdsecurity/http-cve-probing                    ✔️  enabled  0.6      /etc/crowdsec/scenarios/http-cve-probing.yaml                   
 crowdsecurity/http-generic-bf                     ✔️  enabled  0.9      /etc/crowdsec/scenarios/http-generic-bf.yaml                    
 crowdsecurity/http-generic-test                   ✔️  enabled  0.2      /etc/crowdsec/scenarios/http-generic-test.yaml                  
 crowdsecurity/http-open-proxy                     ✔️  enabled  0.5      /etc/crowdsec/scenarios/http-open-proxy.yaml                    
 crowdsecurity/http-path-traversal-probing         ✔️  enabled  0.4      /etc/crowdsec/scenarios/http-path-traversal-probing.yaml        
 crowdsecurity/http-probing                        ✔️  enabled  0.4      /etc/crowdsec/scenarios/http-probing.yaml                       
 crowdsecurity/http-sap-interface-probing          ✔️  enabled  0.1      /etc/crowdsec/scenarios/http-sap-interface-probing.yaml         
 crowdsecurity/http-sensitive-files                ✔️  enabled  0.4      /etc/crowdsec/scenarios/http-sensitive-files.yaml               
 crowdsecurity/http-sqli-probing                   ✔️  enabled  0.4      /etc/crowdsec/scenarios/http-sqli-probing.yaml                  
 crowdsecurity/http-technology-probing             ✔️  enabled  0.1      /etc/crowdsec/scenarios/http-technology-probing.yaml            
 crowdsecurity/http-wordpress-scan                 ✔️  enabled  0.4      /etc/crowdsec/scenarios/http-wordpress-scan.yaml                
 crowdsecurity/http-xss-probing                    ✔️  enabled  0.4      /etc/crowdsec/scenarios/http-xss-probing.yaml                   
 crowdsecurity/jira_cve-2021-26086                 ✔️  enabled  0.4      /etc/crowdsec/scenarios/jira_cve-2021-26086.yaml                
 crowdsecurity/netgear_rce                         ✔️  enabled  0.4      /etc/crowdsec/scenarios/netgear_rce.yaml                        
 crowdsecurity/nginx-req-limit-exceeded            ✔️  enabled  0.3      /etc/crowdsec/scenarios/nginx-req-limit-exceeded.yaml           
 crowdsecurity/pulse-secure-sslvpn-cve-2019-11510  ✔️  enabled  0.4      /etc/crowdsec/scenarios/pulse-secure-sslvpn-cve-2019-11510.yaml 
 crowdsecurity/spring4shell_cve-2022-22965         ✔️  enabled  0.3      /etc/crowdsec/scenarios/spring4shell_cve-2022-22965.yaml        
 crowdsecurity/ssh-bf                              ✔️  enabled  0.3      /etc/crowdsec/scenarios/ssh-bf.yaml                             
 crowdsecurity/ssh-cve-2024-6387                   ✔️  enabled  0.2      /etc/crowdsec/scenarios/ssh-cve-2024-6387.yaml                  
 crowdsecurity/ssh-generic-test                    ✔️  enabled  0.2      /etc/crowdsec/scenarios/ssh-generic-test.yaml                   
 crowdsecurity/ssh-refused-conn                    ✔️  enabled  0.1      /etc/crowdsec/scenarios/ssh-refused-conn.yaml                   
 crowdsecurity/ssh-slow-bf                         ✔️  enabled  0.4      /etc/crowdsec/scenarios/ssh-slow-bf.yaml                        
 crowdsecurity/ssh-time-based-bf                   ✔️  enabled  0.3      /etc/crowdsec/scenarios/ssh-time-based-bf.yaml                  
 crowdsecurity/thinkphp-cve-2018-20062             ✔️  enabled  0.7      /etc/crowdsec/scenarios/thinkphp-cve-2018-20062.yaml            
 crowdsecurity/vmware-cve-2022-22954               ✔️  enabled  0.3      /etc/crowdsec/scenarios/vmware-cve-2022-22954.yaml              
 crowdsecurity/vmware-vcenter-vmsa-2021-0027       ✔️  enabled  0.3      /etc/crowdsec/scenarios/vmware-vcenter-vmsa-2021-0027.yaml      
 ltsich/http-w00tw00t                              ✔️  enabled  0.3      /etc/crowdsec/scenarios/http-w00tw00t.yaml                      
----------------------------------------------------------------------------------------------------------------------------------------
```

### bouncers

`$ cscli bouncers list`

```
------------------------------------------------------------------
 Name  IP Address  Valid  Last API pull  Type  Version  Auth Type 
------------------------------------------------------------------
 web               ✔️                                    api-key   
------------------------------------------------------------------
```

## 3 · La web responde a todo el mundo

### curl desde 10.77.0.50

`$ curl -s -o /dev/null -w '%{http_code}' http://web/`

```
200
```

### curl desde 10.77.0.60

`$ curl -s -o /dev/null -w '%{http_code}' http://web/`

```
200
```

## 4 · Ataque de fuerza bruta por SSH (desde 10.77.0.50)

### 8 contraseñas

`$ for p in ...; do sshpass -p $p ssh root@sshd true; done`

```
21:13:50  intento 123456 -> 5
21:13:54  intento password -> 5
21:13:57  intento admin -> 5
21:14:01  intento root -> 5
21:14:04  intento qwerty -> 5
21:14:08  intento letmein -> 5
21:14:10  intento 111111 -> 5
21:14:13  intento dragon -> 5
```

### lo que quedó en auth.log

`$ grep 'Failed password' /logs/auth.log | tail -3`

```
8
2026-10-07T21:14:09.855767+00:00 bce566a57f7c sshd[22]: Failed password for root from 10.77.0.50 port 37888 ssh2
2026-10-07T21:14:12.630109+00:00 bce566a57f7c sshd[24]: Failed password for root from 10.77.0.50 port 37482 ssh2
2026-10-07T21:14:15.925700+00:00 bce566a57f7c sshd[26]: Failed password for root from 10.77.0.50 port 37490 ssh2
```

### alertas

`$ cscli alerts list`

```
No active alerts
```

### decisiones

`$ cscli decisions list`

```
No active decisions
```

## 4b · La trampa: las IP privadas están en lista blanca

### métricas de lectura

`$ cscli metrics show acquisition`

```
+---------------------------------------------------------------------------------------------------------------+
| Acquisition Metrics                                                                                           |
+---------------------+------------+--------------+----------------+------------------------+-------------------+
| Source              | Lines read | Lines parsed | Lines unparsed | Lines poured to bucket | Lines whitelisted |
+---------------------+------------+--------------+----------------+------------------------+-------------------+
| docker:web          | 6          | 2            | 4              | -                      | 2                 |
| file:/logs/auth.log | 24         | 24           | -              | -                      | 24                |
+---------------------+------------+--------------+----------------+------------------------+-------------------+
```

### la lista blanca por defecto

`$ cat .../parsers/s02-enrich/whitelists.yaml`

```
name: crowdsecurity/whitelists
description: "Whitelist events from private ipv4 addresses"
whitelist:
  reason: "private ipv4/ipv6 ip/ranges"
  ip: 
    - "::1"
  cidr:
    - "127.0.0.0/8"
    - "192.168.0.0/16"
    - "10.0.0.0/8"
    - "172.16.0.0/12"
  # expression:
  #   - "'foo.com' in evt.Meta.source_ip.reverse"
```

### quitarla (solo en el laboratorio)

`$ cscli parsers remove crowdsecurity/whitelists --force`

```
Action plan:
❌ disable
 parsers: crowdsecurity/whitelists

disabling parsers:crowdsecurity/whitelists
```

### el mismo ataque otra vez

`$ for p in ...; do sshpass -p $p ssh root@sshd true; done`

```
21:14:36  intento 123456 -> 5
21:14:40  intento password -> 5
21:14:43  intento admin -> 5
21:14:47  intento root -> 5
21:14:50  intento qwerty -> 5
21:14:54  intento letmein -> 5
21:14:57  intento 111111 -> 5
21:15:01  intento dragon -> 5
```

### alertas

`$ cscli alerts list`

```
+----+---------------+---------------------------+---------+----+-----------+----------------------+----------+
| ID |     value     |           reason          | country | as | decisions |      created_at      |   kind   |
+----+---------------+---------------------------+---------+----+-----------+----------------------+----------+
| 2  | Ip:10.77.0.50 | crowdsecurity/ssh-slow-bf |         |    | ban:1     | 2026-10-07T21:14:36Z | crowdsec |
| 1  | Ip:10.77.0.50 | crowdsecurity/ssh-bf      |         |    | ban:1     | 2026-10-07T21:14:36Z | crowdsec |
+----+---------------+---------------------------+---------+----+-----------+----------------------+----------+
```

### decisiones

`$ cscli decisions list`

```
+----+----------+---------------+---------------------------+--------+---------+----+--------+------------+----------+
| ID |  Source  |  Scope:Value  |           Reason          | Action | Country | AS | Events | expiration | Alert ID |
+----+----------+---------------+---------------------------+--------+---------+----+--------+------------+----------+
| 2  | crowdsec | Ip:10.77.0.50 | crowdsecurity/ssh-slow-bf | ban    |         |    | 11     | 3h59m41s   | 2        |
+----+----------+---------------+---------------------------+--------+---------+----+--------+------------+----------+
1 duplicated entries skipped
```

### y por SSH, ¿ya no entra?

`$ ssh root@sshd (con la contraseña buena)`

```
dentro
codigo=0
Warning: Permanently added 'sshd' (ED25519) to the list of known hosts.
```

## 5 · El bloqueo: la IP baneada tampoco ve la web

### curl desde 10.77.0.50

`$ curl -s -o /dev/null -w '%{http_code}' http://web/`

```
403
```

### curl desde 10.77.0.60

`$ curl -s -o /dev/null -w '%{http_code}' http://web/`

```
200
```

## 6 · Escaneo de la web (desde 10.77.0.60)

### 12 rutas sensibles

`$ for r in /.env /.git/config ...; do curl http://web$r; done`

```
404 /.env
404 /.git/config
404 /wp-login.php
404 /admin
404 /phpmyadmin/
404 /backup.zip
404 /config.php
404 /.aws/credentials
404 /server-status
404 /wp-config.php.bak
404 /db.sql
404 /.htpasswd
```

### alertas

`$ cscli alerts list`

```
+----+---------------+--------------------------------------------+---------+----+-----------+----------------------+----------+
| ID |     value     |                   reason                   | country | as | decisions |      created_at      |   kind   |
+----+---------------+--------------------------------------------+---------+----+-----------+----------------------+----------+
| 5  | Ip:10.77.0.60 | crowdsecurity/http-sensitive-files         |         |    | ban:1     | 2026-10-07T21:15:18Z | crowdsec |
| 4  | Ip:10.77.0.60 | crowdsecurity/http-probing                 |         |    | ban:1     | 2026-10-07T21:15:18Z | crowdsec |
| 3  | Ip:10.77.0.60 | crowdsecurity/http-admin-interface-probing |         |    | ban:1     | 2026-10-07T21:15:18Z | crowdsec |
| 2  | Ip:10.77.0.50 | crowdsecurity/ssh-slow-bf                  |         |    | ban:1     | 2026-10-07T21:14:36Z | crowdsec |
| 1  | Ip:10.77.0.50 | crowdsecurity/ssh-bf                       |         |    | ban:1     | 2026-10-07T21:14:36Z | crowdsec |
+----+---------------+--------------------------------------------+---------+----+-----------+----------------------+----------+
```

### decisiones

`$ cscli decisions list`

```
+----+----------+---------------+------------------------------------+--------+---------+----+--------+------------+----------+
| ID |  Source  |  Scope:Value  |               Reason               | Action | Country | AS | Events | expiration | Alert ID |
+----+----------+---------------+------------------------------------+--------+---------+----+--------+------------+----------+
| 5  | crowdsec | Ip:10.77.0.60 | crowdsecurity/http-sensitive-files | ban    |         |    | 5      | 3h59m54s   | 5        |
| 2  | crowdsec | Ip:10.77.0.50 | crowdsecurity/ssh-slow-bf          | ban    |         |    | 11     | 3h59m25s   | 2        |
+----+----------+---------------+------------------------------------+--------+---------+----+--------+------------+----------+
3 duplicated entries skipped
```

### y ahora la web, desde 10.77.0.60

`$ curl -s -o /dev/null -w '%{http_code}' http://web/`

```
403
```

### una IP limpia sigue entrando

`$ curl desde 10.77.0.70`

```
200
```

## 7 · Quitar un baneo y métricas

### desbanear

`$ cscli decisions delete --ip 10.77.0.50`

```
level=info msg="2 decision(s) deleted"
```

### vuelve a entrar

`$ curl desde 10.77.0.50`

```
200
```

### métricas de lectura

`$ cscli metrics show acquisition parsers`

```
+---------------------------------------------------------------------------------------------------------------+
| Acquisition Metrics                                                                                           |
+---------------------+------------+--------------+----------------+------------------------+-------------------+
| Source              | Lines read | Lines parsed | Lines unparsed | Lines poured to bucket | Lines whitelisted |
+---------------------+------------+--------------+----------------+------------------------+-------------------+
| docker:web          | 31         | 31           | -              | 53                     | -                 |
| file:/logs/auth.log | 32         | 25           | 7              | 75                     | -                 |
+---------------------+------------+--------------+----------------+------------------------+-------------------+
+----------------------------------------------------------------------------+
| Parser Metrics                                                             |
+-------------------------------------------------+------+--------+----------+
| Parsers                                         | Hits | Parsed | Unparsed |
+-------------------------------------------------+------+--------+----------+
| child-crowdsecurity/http-logs                   | 93   | 62     | 31       |
| child-crowdsecurity/nginx-logs                  | 45   | 31     | 14       |
| child-crowdsecurity/sshd-logs                   | 248  | 24     | 224      |
| child-crowdsecurity/sshd-success-logs           | 8    | 1      | 7        |
| child-crowdsecurity/syslog-logs                 | 32   | 32     | -        |
| crowdsecurity/cdn-whitelist                     | 5    | 5      | -        |
| crowdsecurity/dateparse-enrich                  | 56   | 56     | -        |
| crowdsecurity/google-special-crawlers-whitelist | 5    | 5      | -        |
| crowdsecurity/http-logs                         | 31   | 31     | -        |
| crowdsecurity/nginx-logs                        | 31   | 31     | -        |
| crowdsecurity/non-syslog                        | 31   | 31     | -        |
| crowdsecurity/public-dns-allowlist              | 56   | 56     | -        |
| crowdsecurity/rdns                              | 5    | 5      | -        |
| crowdsecurity/seo-bots-whitelist                | 5    | 5      | -        |
| crowdsecurity/sshd-logs                         | 32   | 24     | 8        |
| crowdsecurity/sshd-success-logs                 | 8    | 1      | 7        |
| crowdsecurity/syslog-logs                       | 32   | 32     | -        |
+-------------------------------------------------+------+--------+----------+
```

### memoria

`$ docker stats --no-stream crowdsec web`

```
crowdsec 47.38MiB / 15.36GiB
web 5.848MiB / 15.36GiB
```
