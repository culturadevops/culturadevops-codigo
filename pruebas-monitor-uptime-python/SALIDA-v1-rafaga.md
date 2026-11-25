# SALIDA v1 (con el fallo de la ráfaga) — monitor de disponibilidad en Python (cultura-devops 799)

> ⚠️ PRIMERA versión de monitor.py: el ritmo era `siguiente += INTERVALO; sleep(max(0, siguiente - ahora))`, que se pone al día
> de golpe cuando una revisión tarda más que el intervalo (6 avisos de api en 0,1 s a los 17,1 s); y el motivo de error se sacaba
> del texto (por eso «All connection attempts failed» y «no respondió» para un fallo de conexión). Corregido después; ver SALIDA.md.

> Corrida del 2026-11-05 08:01. python:3.13.17-slim + httpx 0.28.1, cada contenedor con --cpus 1, red local cd799-red.
> Sitios: web (siempre 200) · api (contenedor aparte: se apaga con docker stop y vuelve) · pagos (500 una sí, una no) · lento (tarda 3 s).
> El «Discord» es un servidor FALSO local que imita el webhook (POST JSON → 204; 429 con retry_after si LIMITAR=1).
> No se usa ningún webhook real: nada se envía a Discord.

```
Python 3.13.17 · httpx 0.28.1

$ python monitor.py ingenuo
httpx 0.28.1 · cada 1 s · timeout 2 s · umbral 3 · solo cambios: False · 20 s
  0.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  2.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  2.1 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
  4.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  4.1 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
  6.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  6.1 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
  8.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  8.1 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
  9.1 s  aviso → 🔴 api CAÍDO: no respondió en 2 s (204)
 10.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 10.1 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
 11.1 s  aviso → 🔴 api CAÍDO: no respondió en 2 s (204)
 12.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 12.2 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
 13.1 s  aviso → 🔴 api CAÍDO: no respondió en 2 s (204)
 14.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 14.2 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
 15.1 s  aviso → 🔴 api CAÍDO: no respondió en 2 s (204)
 16.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 16.2 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
 17.1 s  aviso → 🔴 api CAÍDO: no respondió en 2 s (204)
 17.1 s  aviso → 🔴 api CAÍDO: no conecta: All connection attempts failed (204)
 17.1 s  aviso → 🔴 api CAÍDO: no conecta: All connection attempts failed (204)
 17.1 s  aviso → 🔴 api CAÍDO: no conecta: All connection attempts failed (204)
 17.1 s  aviso → 🔴 api CAÍDO: no conecta: All connection attempts failed (204)
 17.1 s  aviso → 🔴 api CAÍDO: no conecta: All connection attempts failed (204)
 17.2 s  aviso → 🔴 api CAÍDO: no conecta: All connection attempts failed (204)
 18.1 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 18.2 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
 20.2 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s (204)
avisos en 20 s: 31  (web 0 · api 11 · pagos 10 · lento 10)

--- lo que vio el Discord falso (su propio reloj) ---
  0.0 s  discord falso escuchando en :9000
  5.3 s  discord ← 🔴 pagos CAÍDO | pagos no responde
  7.3 s  discord ← 🔴 pagos CAÍDO | pagos no responde
  7.3 s  discord ← 🔴 lento CAÍDO | lento no responde
  9.2 s  discord ← 🔴 pagos CAÍDO | pagos no responde
  9.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 10.8 s  ── api se apaga (docker stop cd799-api)
 11.2 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 11.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 13.3 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 13.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 14.2 s  discord ← 🔴 api CAÍDO | api no responde
 15.2 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 15.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 16.3 s  discord ← 🔴 api CAÍDO | api no responde
 17.2 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 17.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 18.3 s  discord ← 🔴 api CAÍDO | api no responde
 19.3 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 19.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 20.2 s  ── api vuelve (docker run cd799-api)
 20.3 s  discord ← 🔴 api CAÍDO | api no responde
 21.3 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 21.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 22.3 s  discord ← 🔴 api CAÍDO | api no responde
 22.3 s  discord ← 🔴 api CAÍDO | api no responde
 22.3 s  discord ← 🔴 api CAÍDO | api no responde
 22.3 s  discord ← 🔴 api CAÍDO | api no responde
 22.3 s  discord ← 🔴 api CAÍDO | api no responde
 22.3 s  discord ← 🔴 api CAÍDO | api no responde
 22.3 s  discord ← 🔴 api CAÍDO | api no responde
 23.3 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 23.3 s  discord ← 🔴 lento CAÍDO | lento no responde
 25.3 s  discord ← 🔴 lento CAÍDO | lento no responde

$ python monitor.py estados
httpx 0.28.1 · cada 1 s · timeout 2 s · umbral 3 · solo cambios: True · 20 s
  6.1 s  429 de Discord: espero 1.5 s y reintento
  7.6 s  aviso → 🔴 lento CAÍDO: no respondió en 2 s · 3 fallos seguidos (204)
 12.1 s  aviso → 🔴 api CAÍDO: no respondió en 2 s · 3 fallos seguidos (204)
 16.1 s  aviso → 🟢 api volvió:  (204)
avisos en 20 s: 3  (web 0 · api 2 · pagos 0 · lento 1)

--- lo que vio el Discord falso (su propio reloj) ---
  0.0 s  discord falso escuchando en :9000
 10.2 s  ── api se apaga (docker stop cd799-api)
 11.6 s  discord ← 429 (límite): le pido que espere 1.5 s
 13.1 s  discord ← 🔴 lento CAÍDO | lento no responde
 17.5 s  discord ← 🔴 api CAÍDO | api no responde
 19.3 s  ── api vuelve (docker run cd799-api)
 21.6 s  discord ← 🟢 api volvió | api responde otra vez

--- el primer aviso, tal cual llegó (GET /recibido) ---
{
  "username": "monitor",
  "content": "🔴 lento CAÍDO",
  "embeds": [
    {
      "title": "lento no responde",
      "description": "no respondió en 2 s · 3 fallos seguidos",
      "color": 15158332,
      "fields": [
        {
          "name": "fallos seguidos",
          "value": "3",
          "inline": true
        },
        {
          "name": "url",
          "value": "http://cd799-sitios:8003/",
          "inline": true
        }
      ],
      "timestamp": "2026-11-05T13:02:40+00:00"
    }
  ]
}

$ python monitor.py rondas
  por rondas, timeout 30 s → web revisado  3 veces en 10 s
  por rondas, timeout 2 s  → web revisado  4 veces en 10 s
  una tarea por sitio, timeout 2 s → web revisado 10 veces en 10 s

$ python monitor.py sin-timeout
timeout por defecto de httpx: Timeout(timeout=5.0)
timeout por defecto de urllib (socket): None
  urlopen sin timeout → lento: 200 OK en 3.0 s
  urlopen sin timeout → lento: 200 OK en 3.0 s

$ DISCORD_WEBHOOK_URL= python monitor.py entorno; echo "salida: $?"
falta DISCORD_WEBHOOK_URL
salida: 1
```
