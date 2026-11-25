# SALIDA — Tailscale vs NetBird vs Headscale (vídeo 340)

Generado 2026-10-12 22:37 UTC con `python correr.py`. Una sola máquina (Docker Desktop, WSL2): el caudal mide el coste del túnel, no una red real. Tailscale como servicio no se mide (pide cuenta).

## 1 · Versiones

### versiones

`$ headscale version; tailscale version; netbird version`

```
headscale version v0.29.4
tailscale 1.102.5
netbird 0.80.0
```

## 2 · Headscale + dos clientes de Tailscale

### arrancar el servidor

`$ docker run headscale/headscale serve`

```
servidor listo en 1.3 s
2026-10-12T22:34:57Z INF starting headscale commit=8106636c7f8d0cf8c9d4fb0beae94415069b768b version=v0.29.4
2026-10-12T22:34:58Z INF listening and serving HTTP on: 0.0.0.0:8080
```

### usuario y clave de alta

`$ headscale users create lab; headscale preauthkeys create -u 1 --reusable`

```
clave: hskey-auth-7Fu… (reutilizable, 2 h)
```

### dos equipos se unen y se hablan

`$ docker run tailscale/tailscale (TS_AUTHKEY, --login-server)`

```
ts2 visible para ts1: 1.9 s desde arrancar los clientes
primer ping por el túnel: 5.5 s después
100.64.0.1  ts1  lab  linux  -                                                 
100.64.0.2  ts2  lab  linux  active; direct 192.168.16.4:39656, tx 836 rx 732
```

### lo que guarda el servidor

`$ headscale nodes list`

```
ID | Hostname | Name | MachineKey | NodeKey | User | Tags | IP addresses      | Ephemeral | Last seen           | Expiration | Connected | Expired
1  | ts1      | ts1  | [2WWgc]    | [Zj+5L] | lab  |      | 100.64.0.1        | false     | 2026-10-12 22:35:03 | N/A        | online    | no     
   |          |      |            |         |      |      | fd7a:115c:a1e0::1 |           |                     |            |           |        
2  | ts2      | ts2  | [9Ge0S]    | [3U5CV] | lab  |      | 100.64.0.2        | false     | 2026-10-12 22:35:03 | N/A        | online    | no     
   |          |      |            |         |      |      | fd7a:115c:a1e0::2 |           |                     |            |           |
```

### ¿a quién más se conecta el cliente?

`$ grep derp config.yaml; tailscale netcheck`

```
config.yaml (por defecto):
    - https://controlplane.tailscale.com/derpmap/default

	* UDP: true
	* Nearest DERP: Miami
```

## 3 · NetBird autoalojado + dos clientes

### arrancar el servidor

`$ docker run netbirdio/netbird-server --config config.yaml`

```
API respondiendo en 14.3 s
combined/cmd/root.go:675:   Exposed address: http://nb-server:80
combined/cmd/root.go:703:   Exposed address: rel://nb-server:80
combined/cmd/root.go:730:     Signal URI: http://nb-server:80
management/server/geolocation/database.go:37: Geolocation database file GeoLite2-City_20260911.mmdb not found, file will be downloaded
management/server/geolocation/database.go:37: Geolocation database file geonames_20260911.db not found, file will be downloaded
```

### administrador y clave de alta

`$ POST /api/setup; POST /api/setup-keys`

```
usuario: admin@lab.internal · token: nbp_fzxx…
clave de alta: 39055E0F-… tipo reusable, válida: True
```

### dos equipos se unen y se hablan

`$ docker run netbirdio/netbird (NB_SETUP_KEY, NB_MANAGEMENT_URL)`

```
nb2 visible para nb1: 1.3 s desde arrancar los clientes
primer ping por el túnel: 5.5 s después
Management: Connected
Signal: Connected
Relays: 2/2 Available
NetBird IP: 100.108.187.116/16
Interface type: Kernel
Lazy connection: true
Peers count: 1/1 Connected
```

### ¿a quién más se conecta el cliente?

`$ netbird status -d`

```
Connection type: P2P
  ICE candidate (Local/Remote): host/host
  Relay server address: rel://nb-server:80
  [stun:nb-server:3478] is Available
  [rel://nb-server:80] is Available via ws
```

### lo que guarda el servidor

`$ GET /api/peers`

```
nb1  100.108.187.116  conectado=True
nb2  100.108.6.69  conectado=True
```

## 4 · El túnel: latencia y caudal (misma máquina)

### los dos van directos antes de medir

`$ tailscale status; netbird status -d`

```
Tailscale: 100.64.0.2  ts2  lab  linux  active; direct 192.168.16.4:39656, tx 1012 rx 860
NetBird:   Connection type: P2P
```

### latencia (20 pings) y caudal (iperf3, 8 s)

`$ ping -c 20; iperf3 -c <ip> -t 8  ×3`

```
Red directa de Docker    ping medio 0.084 ms · iperf3 (3 rondas, Gbit/s): 74.39, 74.35, 74.81 · mediana 74.39
Tailscale + Headscale    ping medio 0.542 ms · iperf3 (3 rondas, Gbit/s): 10.78, 10.65, 10.73 · mediana 10.73
NetBird                  ping medio 0.394 ms · iperf3 (3 rondas, Gbit/s): 2.61, 2.68, 2.67 · mediana 2.67
```

### tipo de interfaz

`$ ip link; netbird status`

```
tailscale0: link/none  promiscuity 0 allmulti 0 minmtu 68 maxmtu 65535 
    tun type tun pi off vnet_hdr on persist off addrgenmode random numtxqueues 1 numrxqueues 1 gso_max_size 65536 gso_max_segs 65535 tso_max_size 65536 tso_max_segs 65535 gro_max_size 65536 gso_ipv4_max_size 65536 gro_ipv4_max_size 65536
Interface type: Kernel
```

## 5 · Lo que corre en tu servidor

### memoria en reposo (2 equipos unidos)

`$ docker stats --no-stream`

```
headscale 17.36MiB / 15.36GiB
nb-server 90.98MiB / 15.36GiB
ts1 77.47MiB / 15.36GiB
nb1 29.01MiB / 15.36GiB
```

### tamaño de las imágenes

`$ docker image inspect -f {{.Size}}`

```
headscale/headscale:latest           31.9 MB
netbirdio/netbird-server:latest      93.3 MB
tailscale/tailscale:latest           60.5 MB
netbirdio/netbird:latest             22.4 MB
```

## 6 · Anexo: dónde se decide el DERP en Headscale

### config.yaml, bloque derp (por defecto)

`$ grep -A… derp: config.yaml`

```
derp:
  server:
    enabled: false
    stun_listen_addr: "0.0.0.0:3478"
    automatically_add_embedded_derp_region: true
  urls:
    - https://controlplane.tailscale.com/derpmap/default
  auto_update_enabled: true
```
