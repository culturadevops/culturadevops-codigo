# instalar-victima.ps1 - convierte ESTE Windows en la victima de la leccion 09, por fases.
#
# ASCII A PROPOSITO (canon: los .ps1 sin tildes). Requiere ADMINISTRADOR (lo pide el MSI y el
# driver de Sysmon). Se lanza con:  Start-Process powershell -Verb RunAs -ArgumentList '-File ...'
#
#   -Fase sin   1. instala el agente de Wazuh 4.9.2 (la MISMA version que el manager: 4.14 la
#                  rechaza, tropiezo 4 del LEEME) apuntando a 127.0.0.1, donde Docker publica
#                  1514/1515. Lo arranca. Y MIDE la accion sin Sysmon.
#   -Fase con   2. instala Sysmon64 con la config de SwiftOnSecurity, le dice al agente que lea
#                  el canal de Sysmon (NO viene de fabrica), lo reinicia. Y MIDE con Sysmon.
#   -Quitar     deshace todo.
param([ValidateSet('sin','con')][string]$Fase = 'sin', [switch]$Quitar)
$ErrorActionPreference = 'Stop'
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$msi = Join-Path $aqui 'wazuh-agent-4.9.2-1.msi'
$sysmon = Join-Path $aqui 'sysmon\Sysmon64.exe'
$cfg = Join-Path $aqui 'sysmonconfig-swiftonsecurity.xml'
$log = Join-Path $aqui '_instalar.log'
$ossec = 'C:\Program Files (x86)\ossec-agent\ossec.conf'

function Marca($t) { $l = "$(Get-Date -Format 'HH:mm:ss') $t"; Write-Host $l; Add-Content $log $l }

try {
if ($Quitar) {
  if (Get-Service Sysmon64 -ErrorAction SilentlyContinue) { Marca "Sysmon -u"; & $sysmon -accepteula -u force | Out-Null }
  Marca "desinstalando agente"; Start-Process msiexec -Wait -ArgumentList "/x `"$msi`" /qn"
  Marca "hecho: maquina limpia"; exit 0
}

if ($Fase -eq 'sin') {
  Marca "1. agente de Wazuh 4.9.2 -> manager 127.0.0.1"
  Start-Process msiexec -Wait -ArgumentList "/i `"$msi`" /qn WAZUH_MANAGER=`"127.0.0.1`" WAZUH_REGISTRATION_SERVER=`"127.0.0.1`" WAZUH_AGENT_NAME=`"victima-windows`""
  Start-Service WazuhSvc
  Marca ("   servicio WazuhSvc: " + (Get-Service WazuhSvc).Status)
  Marca "   esperando 30 s a que enrole y conecte"
  Start-Sleep -Seconds 30
  Marca "   midiendo SIN Sysmon"
  & (Join-Path $aqui 'medir-leccion-09.ps1') -Fase sin
  Marca "fase 1 hecha"
  exit 0
}

Marca "2. Sysmon64 con sysmonconfig-swiftonsecurity.xml"
& $sysmon -accepteula -i $cfg | Out-Null
Marca ("   servicio Sysmon64: " + (Get-Service Sysmon64).Status)

Marca "3. el agente NO lee el canal de Sysmon de fabrica: se le anade el localfile"
$conf = Get-Content $ossec -Raw
if ($conf -notmatch 'Microsoft-Windows-Sysmon/Operational') {
  $bloque = "  <localfile>`r`n    <location>Microsoft-Windows-Sysmon/Operational</location>`r`n    <log_format>eventchannel</log_format>`r`n  </localfile>`r`n</ossec_config>"
  $i = $conf.LastIndexOf('</ossec_config>')
  $conf = $conf.Substring(0, $i) + $bloque + $conf.Substring($i + '</ossec_config>'.Length)
  Set-Content $ossec $conf -Encoding UTF8
  Marca "   localfile anadido al final de ossec.conf"
} else { Marca "   ya estaba" }
Restart-Service WazuhSvc
Marca ("   servicio WazuhSvc: " + (Get-Service WazuhSvc).Status)
Marca "   esperando 30 s a que reconecte"
Start-Sleep -Seconds 30
Marca "   midiendo CON Sysmon"
& (Join-Path $aqui 'medir-leccion-09.ps1') -Fase con
Marca "fase 2 hecha: victima Windows completa (agente + Sysmon)"
} catch {
  Marca ("ERROR: " + $_.Exception.Message)
  exit 1
}
