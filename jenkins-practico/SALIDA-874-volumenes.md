# SALIDA 874 (complemento) — volúmenes de la imagen del agente

> Corrida del 2026-11-18 09:35.

```
$ docker image inspect jenkins/agent:3395.v6e5377b_0fb_3c-5-jdk21 --format '{{json .Config.Volumes}}'
{"/home/jenkins/.jenkins":{},"/home/jenkins/agent":{}}
$ docker run -d --name jk-a-sin-removevolumes jenkins/agent:3395.v6e5377b_0fb_3c-5-jdk21 sleep 1 ; docker rm jk-a-sin-removevolumes   # borrar SIN -v
volúmenes huérfanos nuevos: 2
(borrado a mano: volumen anónimo d17ab4618218…)
(borrado a mano: volumen anónimo 0016796512ed…)
```
