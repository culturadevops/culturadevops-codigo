# SALIDA — Netdata (vídeo 334)

Generado 2026-10-12 23:51 UTC con `python correr.py`. Imagen netdata/netdata:stable; mide la VM de Docker Desktop (Linux) donde corren los contenedores.

## 1 · Instalar: el docker run oficial

### arranque

`$ docker run -d --name netdata ... netdata/netdata:stable`

```
API respondiendo en 1 s
```

### versión y sistema

`$ curl /api/v1/info`

```
{
 "version": "v2.12.0",
 "os_name": "unknown",
 "os_version": "unknown",
 "kernel_version": "6.18.33.2-microsoft-standard-WSL2",
 "cores_total": "24",
 "total_disk_space": "1104495886336",
 "ram_total": "16487469056"
}
```

### lo que mide sin configurar nada

`$ curl /api/v1/charts`

```
1156 gráficas, 3330 métricas (dimensiones)
app                  224
cgroup               202
net                  171
netdata              131
docker               88
disk                 87
user                 42
usergroup            42
system               39
netflow              28
ipv6                 26
mem                  25
```

### frecuencia

`$ update_every de system.cpu`

```
1 s
```

### memoria y CPU de netdata

`$ docker stats --no-stream netdata`

```
netdata 137.8MiB / 15.36GiB 2.15%
```

### alertas cargadas

`$ curl /api/v1/alarms?all | contar`

```
318 alertas configuradas de serie (+ la mía)
```

### la alerta por defecto de CPU

`$ health.d/cpu.conf (10min_cpu_usage)`

```
template: 10min_cpu_usage
         on: system.cpu
      class: Utilization
       type: System
  component: CPU
host labels: _os=linux
     lookup: average -10m unaligned of user,system,softirq,irq,guest
      units: %
      every: 1m
       warn: $this > (($status >= $WARNING)  ? (75) : (85))
       crit: $this > (($status == $CRITICAL) ? (85) : (95))
      delay: down 15m multiplier 1.5 max 1h
    summary: System CPU utilization
       info: Average CPU utilization over the last 10 minutes (excluding iowait, nice and steal)
         to: sysadmin
```

### mi alerta de prueba

`$ cat health.d/cpu_demo.conf`

```
alarm: cpu_30s_demo
    on: system.cpu
lookup: average -30s unaligned of user,system,softirq,irq,guest
 units: %
 every: 10s
  warn: $this > 50
  crit: $this > 80
  info: CPU media de los últimos 30 segundos (alerta de prueba)
    to: sysadmin
```

### estado en reposo

`$ CPU media 30 s; alertas activas`

```
CPU 15.2 %
(ninguna activa)
```

## 2 · Carga de CPU

### lanzar la carga

`$ 24 contenedores con un bucle infinito (uno por núcleo)`

```
lanzados a las 23:48:27 UTC
```

### cada 10 s

`$ CPU media 30 s y alertas activas`

```
t=   0s  CPU(30s)=18.9 %  (ninguna activa)
t=  10s  CPU(30s)=18.9 %  (ninguna activa)
t=  20s  CPU(30s)=18.9 %  cpu_30s_demo                 WARNING   79.5%  system.cpu
t=  30s  CPU(30s)=98.4 %  cpu_30s_demo                 CRITICAL  99.2%  system.cpu
t=  40s  CPU(30s)=98.4 %  cpu_30s_demo                 CRITICAL  99.4%  system.cpu
t=  50s  CPU(30s)=98.4 %  cpu_30s_demo                 CRITICAL  99.5%  system.cpu
t=  60s  CPU(30s)=99.5 %  cpu_30s_demo                 CRITICAL  99.5%  system.cpu
```

## 3 · Lo que llegó a ntfy

### alertas en ntfy

`$ curl ntfy/alertas/json?poll=1`

```
23:48:44  prio=4  29b2aa416a9b: cpu 30s demo | 29b2aa416a9b needs attention: cpu 30s demo = 54.3% - CPU media de los últimos 30 segundos (alerta de
23:49:03  prio=5  29b2aa416a9b: cpu 30s demo | 29b2aa416a9b is critical: cpu 30s demo = 99.2% - CPU media de los últimos 30 segundos (alerta de pru
```

## 4 · Quitar la carga y recuperarse

### cada 10 s

`$ CPU media 30 s y alertas activas`

```
t=   0s  CPU(30s)=99.3 %  cpu_30s_demo                 CRITICAL  99.3%  system.cpu | system_clock_sync_state      WARNING   0 synchronization state  system.clock_sync_state
t=  10s  CPU(30s)=68.5 %  cpu_30s_demo                 CRITICAL  90.8%  system.cpu
t=  20s  CPU(30s)=68.5 %  cpu_30s_demo                 WARNING   62.8%  system.cpu
t=  30s  CPU(30s)=68.5 %  (ninguna activa)
```

## 5 · El registro de alertas (CPU ya baja)

### /api/v1/alarm_log de cpu_30s_demo

`$ el ciclo WARNING → CRITICAL → CLEAR`

```
23:46:58   REMOVED → UNINITIALIZED -
23:46:58  UNINITIALIZED → REMOVED  -
23:46:58   REMOVED → UNINITIALIZED -
23:47:23  UNINITIALIZED → CLEAR    15.2%
23:48:43     CLEAR → WARNING  54.3%
23:49:03   WARNING → CRITICAL 99.2%
23:50:33  CRITICAL → WARNING  62.8%
23:50:43   WARNING → CLEAR    34.7%
```
