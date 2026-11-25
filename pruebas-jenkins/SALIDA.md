# SALIDA — Jenkins LTS contra Woodpecker, medidos en esta máquina

> Corrida del 2026-08-30. ⛔ Ninguna cifra de blog. Jenkins recién instalado, CERO trabajos y
> CERO plugins extra (la comparación más generosa posible con Jenkins: el de verdad lleva
> decenas de plugins y crece desde aquí). Woodpecker es el del laboratorio del canal
> (`lab-woodpecker` + `lab-woodpecker-agente`, v3.11.0), vivo desde la serie «alternativa a».

| | Jenkins LTS | Woodpecker v3.11 (server + agente) |
|---|---|---|
| imagen | 289,9 MB descarga (289.866.931 B) | 70 MB + 70,5 MB (en disco) |
| listo (página de login) | 6 s | — (ya corría) |
| **RAM en vacío** | **648,2 MiB** (recién listo) · **649,1 MiB** (30 s después) | **58,4 + 38,6 = 97,0 MiB** |
| ratio de RAM | **6,7x** más que Woodpecker completo | |

⚠️ Lectura honesta: es un Jenkins VACÍO — sin un solo plugin de los que lo hacen útil y sin
un solo job. 649 MiB es su punto de partida, no su techo. La crítica de plugins/Groovy/CVEs
va como criterio con fuente en pantalla, sin inventar números.
