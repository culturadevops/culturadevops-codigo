# Tu primera regla de Wazuh: el decoder, el XML roto y el fichero que nadie leía — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · la línea de mi aplicación

```console
Aug 27 18:03:11 victima miapp[8123]:
  LOGIN_FAIL user=ana ip=10.0.0.7
  reason=bad_password
```

## 2. en mi máquina · sin decoder

```console
Phase 1: program_name: 'miapp'

Phase 2: Completed decoding.
No decoder matched.
```

## 3. en mi máquina · local_decoder.xml

```console
<decoder name="miapp">
  <program_name>miapp</program_name>
</decoder>

<decoder name="miapp-login">
  <parent>miapp</parent>
  <regex>LOGIN_FAIL user=(\w+) ip=(\S+)</regex>
  <order>dstuser, srcip</order>
</decoder>
```

## 4. en mi máquina · el fallo, a propósito

```console
  <order>dstuser, srcip
</decoder>

      ↑ falta </order>
```

## 5. en mi máquina · lo que salió, literal

```console
** Wazuh-logtest error -1:
ERROR: (1226): Error reading XML file
  'etc/decoders/local_decoder.xml':
  XMLERR: Element 'order' not closed. (line 9).
ERROR: (7311): Failure to initializing session
```

## 6. en mi máquina · con el decoder arreglado

```console
Phase 2: Completed decoding.
  name:     'miapp'
  dstuser:  'ana'
  srcip:    '10.0.0.7'
```

## 7. en mi máquina · local_rules.xml

```console
<rule id="100101" level="7">
  <if_sid>100100</if_sid>
  <regex>LOGIN_FAIL</regex>
  <description>miapp: login fallido
     de $(dstuser) desde $(srcip)</description>
</rule>
```

## 8. en mi máquina · y esto es lo que salió

```console
Phase 3: Completed filtering (rules).
  id:          '100101'
  level:       '7'
  description: 'miapp: login fallido
                de ana desde 10.0.0.7'

**Alert to be generated.
```

## 9. en mi máquina · la regla que cuenta

```console
<rule id="100102" level="10"
      frequency="5" timeframe="60">
  <if_matched_sid>100101</if_matched_sid>
  <same_srcip />
</rule>
```

## 10. en mi máquina · todo lo que vigilaba el agente

```console
<location>/var/log/auth.log</location>
<location>/var/log/dpkg.log</location>
<location>.../active-responses.log</location>

y /var/log/syslog no está
```

## 11. en mi máquina · lo que había en el registro

```console
17:09:10 victima miapp:
  LOGIN_FAIL user=ana ip=10.0.0.7

message repeated 17 times
```

## 12. en mi máquina · seis líneas distintas

```console
5 x Rule 100101 (nivel 7)
      'miapp: login fallido de ana...'
      'miapp: login fallido de bruno...'

1 x Rule 100102 (nivel 10)
      '5 logins fallidos desde la misma IP'
```

## 13. en mi máquina · la alerta de nivel 10, entera

```console
Rule: 100102 (level 10)
Src IP: 10.0.0.7   User: diego

  17:21:30  LOGIN_FAIL user=diego
  17:21:29  LOGIN_FAIL user=clara
  17:21:28  LOGIN_FAIL user=bruno
  17:21:27  LOGIN_FAIL user=ana
```
