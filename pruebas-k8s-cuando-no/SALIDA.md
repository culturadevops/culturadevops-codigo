# SALIDA — Lo que cuesta Kubernetes vacío, medido en esta máquina

> Corrida del 2026-08-30. ⛔ Ninguna cifra de blog. Clúster: k3s (la distribución ligera de
> Kubernetes) como UN contenedor (`rancher/k3s:latest server`, --privileged) en Docker 29.6.2.
> Referencia: la misma API de Flask del vídeo 153 (`cdo-dockerpy-2-slim:1`) corriendo sola.

| | |
|---|---|
| imagen de k3s | 81,3 MB de descarga (81.330.204 B) |
| nodo Ready | **9 s** desde el docker run |
| pods de sistema al asentarse | 7 (coredns, traefik, metrics-server, local-path, svclb, 2 helm-install Completed) |
| **RAM del clúster VACÍO** | **688,7 MiB** (docker stats, asentado) |
| CPU del clúster vacío, en reposo | 3,52 % |
| la misma API de Flask sola (docker run) | **32,4 MiB** |
| ratio | **21x**: el clúster vacío pesa 21 veces más que la app que serviría |

⚠️ Lectura honesta: k3s es la distribución LIGERA; un clúster gestionado o kubeadm pesa más,
no menos (se dice como criterio, sin cifra). Y esos 688 MiB compran cosas reales: reinicios,
réplicas, salud, service discovery — el vídeo lista qué, y cuándo lo necesitas de verdad.
