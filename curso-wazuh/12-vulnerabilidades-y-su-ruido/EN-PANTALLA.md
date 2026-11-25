# 9,3 GB de catálogo y cero resultados: cuatro días con un módulo caído — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · la configuración del módulo

```console
<vulnerability-detection>
  <enabled>yes</enabled>
  <index-status>yes</index-status>
  <feed-update-interval>60m</feed-update-interval>
</vulnerability-detection>
```

## 2. en mi máquina · la única pista

```console
indexer-connector: WARNING:
IndexerConnector initialization failed
for index 'wazuh-states-vulnerabilities-...'
retrying until the connection is successful.
```

## 3. en mi máquina · la carpeta que no existe

```console
$ ls /etc/filebeat/certs/
ls: cannot access '/etc/filebeat/certs/':
    No such file or directory

estaban en /etc/ssl/
```

## 4. en mi máquina · la tercera capa

```console
el certificado dice:  CN = wazuh.manager
y el almacén autoriza: CN = admin

HTTP 401
```

## 5. en mi máquina · por fin

```console
IndexerConnector initialized successfully
for index: wazuh-states-vulnerabilities
```

## 6. en mi máquina · las diez, tal cual

```console
CVE-2016-2781   Low     coreutils
CVE-2024-2236   Medium  libgcrypt20
CVE-2023-50782  High    cryptography 41.0.7
CVE-2024-26130  High    cryptography 41.0.7
CVE-2024-0727   Medium  cryptography 41.0.7
CVE-2023-50782  High    cryptography 41.0.7
CVE-2024-26130  High    cryptography 41.0.7
CVE-2024-0727   Medium  cryptography 41.0.7
CVE-2024-41996  High    openssl
CVE-2021-31879  Medium  wget
```

## 7. en mi máquina · el aviso que sigue ahí

```console
indexer-connector: WARNING:
  Failed to sync agent '005' with the indexer.
```
