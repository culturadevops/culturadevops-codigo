# verificar-09.ps1 - comprobaciones de la leccion 09 que necesitan ADMINISTRADOR.
# ASCII A PROPOSITO. Deja la salida en _verificado-09.txt.
#   1. Quien lanzo net.exe (las alertas 92039 "account discovery"): padre de cada proceso.
#   2. Cuantos eventos ha escrito Sysmon desde que se instalo, por id.
#   3. La politica de auditoria de creacion de procesos (por que 4688 da 0).
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$salida = Join-Path $aqui '_verificado-09.txt'
if (Test-Path $salida) { Remove-Item $salida }
function W($t) { Write-Host $t; Add-Content -Path $salida -Value $t -Encoding UTF8 }

W "== verificacion leccion 09 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
W "-- 1. procesos net.exe / net1.exe vistos por Sysmon (imagen <- padre | linea de comando):"
try {
  Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'; Id=1} -ErrorAction Stop | ForEach-Object {
    $x = [xml]$_.ToXml(); $d = @{}; $x.Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }
    if ($d['Image'] -match 'net1?\.exe$') { W ("   " + $d['Image'] + "  <-  " + $d['ParentImage'] + "  |  " + $d['CommandLine']) }
  }
} catch { W ("   error: " + $_.Exception.Message.Split([char]10)[0]) }

W "-- 2. eventos de Sysmon por id desde la instalacion:"
try {
  Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Sysmon/Operational'} -ErrorAction Stop | Group-Object Id | Sort-Object Count -Descending | ForEach-Object { W ("   id " + $_.Name + ": " + $_.Count) }
} catch { W ("   error: " + $_.Exception.Message.Split([char]10)[0]) }

W "-- 3. auditpol, creacion de procesos:"
$a = auditpol /get /subcategory:"{0CCE922B-5D45-4CB6-A87A-9DB16A9BF5BE}" 2>&1
$a | ForEach-Object { if ("$_".Trim()) { W ("   " + "$_".Trim()) } }
W "-- 4. version de Sysmon:"
$v = & (Join-Path $aqui 'sysmon\Sysmon64.exe') -c 2>&1 | Select-Object -First 3
$v | ForEach-Object { W ("   " + "$_".Trim()) }
W "[ok]"
