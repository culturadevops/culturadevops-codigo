# Respuesta activa: que bloquee la IP solo, y por qué asusta — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · los comandos de fábrica

```console
disable-account     restart-wazuh
firewall-drop       host-deny
route-null          win_route-null
netsh
```

## 2. en mi máquina · el bloque, tal cual viene

```console
<active-response>
  active-response options here
</active-response>
```

## 3. en mi máquina · lo que añado

```console
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5763</rules_id>
  <timeout>120</timeout>
</active-response>
```

## 4. en mi máquina · fallo uno

```console
$ which iptables

(nada)
```

## 5. en mi máquina · fallo dos

```console
$ iptables -L INPUT -n
Could not fetch rule set generation id:
Permission denied (you must be root)
```

## 6. en mi máquina · las dos líneas

```console
2 IPs in the white list for active response.
1 Hostname(s) in the white list.
```

## 7. en mi máquina · la lista blanca, de fábrica

```console
<global>
  <white_list>127.0.0.1</white_list>
  <white_list>^localhost.localdomain$</white_list>
  <white_list>172.31.0.2</white_list>
</global>
```
