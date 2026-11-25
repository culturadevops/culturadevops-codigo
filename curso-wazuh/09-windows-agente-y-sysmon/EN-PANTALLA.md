# Windows: el agente y Sysmon, donde está la telemetría buena — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi Windows · PowerShell como administrador

```console
PS> msiexec /i wazuh-agent-4.9.2-1.msi /qn `
PS>   WAZUH_MANAGER=127.0.0.1 WAZUH_REGISTRATION_SERVER=127.0.0.1 `
PS>   WAZUH_AGENT_NAME=victima-windows
PS> Start-Service WazuhSvc

Status   Name       DisplayName
Running  WazuhSvc   Wazuh
```

## 2. en el manager · agent_control -l

```console
Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh.manager (server), IP: 127.0.0.1, Active/Local
   ID: 006, Name: victima, IP: any, Disconnected
   ID: 007, Name: victima-windows, IP: any, Active
```

## 3. las 401, agrupadas por regla

```console
269  19007 nivel 7  CIS Windows 11 Benchmark: Ensure ...
114  19008 nivel 3  CIS Windows 11 Benchmark: Ensure ...
  8  19009 nivel 3  CIS Windows 11 Benchmark: Ensure ...
  2  19005 nivel 9  SCA summary: Score less than 30% (29)
  1  60106 nivel 3  Windows Logon Success
  1  501   nivel 3  New wazuh agent connected.
```

## 4. en mi Windows · la misma acción, cinco veces

```console
PS> 1..5 | ForEach-Object { cmd.exe /c whoami }
desktop-ofd60uf\user
desktop-ofd60uf\user
...
```

## 5. el Visor de eventos, a mano

```console
PS> Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688}
No se encontraron eventos que coincidan con los criterios.
PS> Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'}
No hay un registro de eventos que coincida con
"Microsoft-Windows-Sysmon/Operational".
```

## 6. en mi Windows · instalar Sysmon

```console
PS> .\Sysmon64.exe -accepteula -i sysmonconfig-swiftonsecurity.xml

Status   Name       DisplayName
Running  Sysmon64   Sysmon64
```

## 7. ossec.conf del agente · lo que falta

```console
<localfile>
  <location>Microsoft-Windows-Sysmon/Operational</location>
  <log_format>eventchannel</log_format>
</localfile>

$ Restart-Service WazuhSvc
```

## 8. lo que llegó · las 10 nuevas

```console
5  92004 nivel 4  Powershell process spawned Windows
                  command shell instance
5  92032 nivel 3  Suspicious Windows cmd shell execution
```

## 9. el canal de Sysmon · quién lanzó qué

```console
docker.exe  <-  Docker Desktop.exe  |  docker stats --all --no-stream
docker.exe  <-  Docker Desktop.exe  |  docker stats --all --no-stream
cmd.exe     <-  powershell.exe      |  cmd.exe /c whoami
whoami.exe  <-  cmd.exe             |  whoami
...
```
