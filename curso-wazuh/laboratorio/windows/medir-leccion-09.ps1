# medir-leccion-09.ps1 - la MISMA accion, dos veces: sin Sysmon y con Sysmon.
#
# ASCII A PROPOSITO (canon). Leer el registro Security y auditpol piden ADMINISTRADOR.
# No ataca nada: la accion es un proceso lanzando otro (PowerShell lanza cmd.exe, que lanza
# whoami), en esta maquina, N veces.
#
#   .\medir-leccion-09.ps1 -Fase sin      # con el agente instalado y Sysmon todavia NO
#   .\medir-leccion-09.ps1 -Fase con      # con Sysmon instalado
#
# Cuenta desde el manager (por-regla.sh dentro del contenedor) las alertas del agente
# victima-windows ANTES y 40 s DESPUES (el agente manda por lotes: contar al momento da cero,
# leccion 08). Deja la salida literal en _medido-09-<fase>.txt: de ahi salen las cifras.
param([ValidateSet('sin','con')][string]$Fase = 'sin', [int]$Veces = 5)
$ErrorActionPreference = 'Continue'
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$salida = Join-Path $aqui "_medido-09-$Fase.txt"
$env:MSYS_NO_PATHCONV = '1'
$sh = Join-Path $aqui 'por-regla.sh'
docker cp $sh lab-wazuh-manager:/tmp/por-regla.sh | Out-Null

function W($t) { Write-Host $t; Add-Content -Path $salida -Value $t -Encoding UTF8 }
function Total { (docker exec lab-wazuh-manager sh /tmp/por-regla.sh total | Select-Object -Last 1).Trim() }

if (Test-Path $salida) { Remove-Item $salida }
$sys = Get-Service Sysmon64 -ErrorAction SilentlyContinue
W "== leccion 09 - fase: $Fase - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
W ("agente WazuhSvc: " + (Get-Service WazuhSvc).Status + " - Sysmon64: " + $(if ($sys) { $sys.Status } else { 'no instalado' }))
$antes = Total
W "-- antes: $antes alertas del agente victima-windows"
W "-- accion: $Veces veces PowerShell -> cmd.exe /c whoami"
$t0 = Get-Date
1..$Veces | ForEach-Object { cmd.exe /c whoami | Out-Null; Start-Sleep -Milliseconds 300 }
W "-- esperando 40 s (el agente manda por lotes)"
Start-Sleep -Seconds 40
$despues = Total
W "-- despues: $despues alertas del agente victima-windows (nuevas: $([int]$despues - [int]$antes))"
W "-- por regla (acumulado del agente):"
docker exec lab-wazuh-manager sh /tmp/por-regla.sh reglas | ForEach-Object { W "   $_" }
W "-- las 8 ultimas alertas del agente:"
docker exec lab-wazuh-manager sh /tmp/por-regla.sh ultimas 8 | ForEach-Object { W "   $_" }

W "-- Visor de eventos, canal Sysmon, id 1 (creacion de proceso) desde la accion:"
try {
  $n = (Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=1; StartTime=$t0} -ErrorAction Stop | Measure-Object).Count
  W "   $n"
  Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=1; StartTime=$t0} -MaxEvents 3 -ErrorAction Stop | ForEach-Object {
    $x = [xml]$_.ToXml(); $d = @{}; $x.Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }
    W ("   " + $d['Image'] + "  <-  " + $d['ParentImage'] + "  |  " + $d['CommandLine'])
  }
} catch { W ("   0 - " + $_.Exception.Message.Split([char]10)[0]) }

W "-- Visor de eventos, Security, id 4688 (creacion de proceso) desde la accion:"
try {
  $n2 = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688; StartTime=$t0} -ErrorAction Stop | Measure-Object).Count
  W "   $n2"
} catch { W ("   0 - " + $_.Exception.Message.Split([char]10)[0]) }

W "-- politica de auditoria (auditpol) para creacion de procesos:"
auditpol /get /subcategory:"{0CCE922B-5D45-4CB6-A87A-9DB16A9BF5BE}" 2>&1 | Where-Object { "$_".Trim() -ne '' } | Select-Object -Last 1 | ForEach-Object { W "   $("$_".Trim())" }
W "[ok] guardado en $salida"
