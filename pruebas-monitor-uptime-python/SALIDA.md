# SALIDA — monitor de disponibilidad en Python (cultura-devops 799)

> Corrida del 2026-11-05 08:05. python:3.13.17-slim + httpx 0.28.1, cada contenedor con --cpus 1, red local cd799-red.
> Sitios: web (siempre 200) · api (contenedor aparte: se apaga con docker stop y vuelve) · pagos (500 una sí, una no) · lento (tarda 3 s).
> El «Discord» es un servidor FALSO local que imita el webhook (POST JSON → 204; 429 con retry_after si LIMITAR=1).
> No se usa ningún webhook real: nada se envía a Discord.

```
Python 3.13.17 · httpx 0.28.1

$ python monitor.py ingenuo
httpx 0.28.1 · cada 1 s · timeout 2 s · umbral 3 · solo cambios: False · 20 s
  0.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  2.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  2.0 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s (204)
  4.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  5.0 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s (204)
  6.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  7.0 s  aviso → 🔴 api CAÍDO: conexión rechazada (204)
  8.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
  8.0 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s (204)
 10.0 s  aviso → 🔴 api CAÍDO: no conectó en 2 s (204)
 10.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 11.0 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s (204)
 12.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 13.0 s  aviso → 🔴 api CAÍDO: no conectó en 2 s (204)
 14.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 14.0 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s (204)
 16.0 s  aviso → 🔴 api CAÍDO: no conectó en 2 s (204)
 16.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 17.0 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s (204)
 18.0 s  aviso → 🔴 pagos CAÍDO: HTTP 500 (204)
 20.0 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s (204)
avisos en 20 s: 21  (web 0 · api 4 · pagos 10 · lento 7)

--- lo que vio el Discord falso (su propio reloj) ---
  0.0 s  discord falso escuchando en :9000
  2.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
  4.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
  4.6 s  discord ← 🔴 lento CAÍDO | lento no responde
  6.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
  7.6 s  discord ← 🔴 lento CAÍDO | lento no responde
  8.5 s  ── api se apaga (docker stop cd799-api)
  8.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
  9.6 s  discord ← 🔴 api CAÍDO | api no responde
 10.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 10.6 s  discord ← 🔴 lento CAÍDO | lento no responde
 12.6 s  discord ← 🔴 api CAÍDO | api no responde
 12.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 13.6 s  discord ← 🔴 lento CAÍDO | lento no responde
 14.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 15.6 s  discord ← 🔴 api CAÍDO | api no responde
 16.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 16.6 s  discord ← 🔴 lento CAÍDO | lento no responde
 17.0 s  ── api vuelve (docker run cd799-api)
 18.6 s  discord ← 🔴 api CAÍDO | api no responde
 18.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 19.6 s  discord ← 🔴 lento CAÍDO | lento no responde
 20.6 s  discord ← 🔴 pagos CAÍDO | pagos no responde
 22.6 s  discord ← 🔴 lento CAÍDO | lento no responde

$ python monitor.py estados
httpx 0.28.1 · cada 1 s · timeout 2 s · umbral 3 · solo cambios: True · 20 s
  8.0 s  429 de Discord: espero 1.5 s y reintento
  9.5 s  aviso → 🔴 lento CAÍDO: conectó, pero no respondió en 2 s · 3 fallos seguidos (204)
 16.0 s  aviso → 🔴 api CAÍDO: no conectó en 2 s · 3 fallos seguidos (204)
 17.0 s  aviso → 🟢 api volvió:  (204)
avisos en 20 s: 3  (web 0 · api 2 · pagos 0 · lento 1)

--- lo que vio el Discord falso (su propio reloj) ---
  0.0 s  discord falso escuchando en :9000
  8.5 s  ── api se apaga (docker stop cd799-api)
 10.7 s  discord ← 429 (límite): le pido que espere 1.5 s
 12.2 s  discord ← 🔴 lento CAÍDO | lento no responde
 17.9 s  ── api vuelve (docker run cd799-api)
 18.7 s  discord ← 🔴 api CAÍDO | api no responde
 19.7 s  discord ← 🟢 api volvió | api responde otra vez

--- el primer aviso, tal cual llegó (GET /recibido) ---
{
  "username": "monitor",
  "content": "🔴 lento CAÍDO",
  "embeds": [
    {
      "title": "lento no responde",
      "description": "conectó, pero no respondió en 2 s · 3 fallos seguidos",
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
      "timestamp": "2026-11-05T13:05:46+00:00"
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
