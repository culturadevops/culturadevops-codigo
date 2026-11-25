# Salida ejecutada — vídeo 230 «Nomad, ¿la alternativa a Kubernetes este 2026?»

> Corrida del 2026-09-09. Nomad 1.9 contra k3s v1.31.3, cada uno en su contenedor, levantando
> **el mismo servicio**: 2 réplicas de un servidor web. Reproducible con `bash demo.sh`.

---

## ⚠️ La elección que hay que decir en voz alta

Se compara Nomad contra **k3s**, no contra un Kubernetes de tres maestros ni contra un servicio
gestionado. Motivo: k3s es la comparación **justa** — una sola pieza, pensada para lo mismo que un
Nomad de un nodo. Contra un clúster de producción sería tramposo en un sentido; contra un
gestionado, en el otro.

## ✅ Los dos llegaron al mismo estado

```
   nginx que ve el Docker de la maquina (los de Nomad):  2
   nginx dentro del containerd de k3s:                   2
   k3s, réplicas listas:                                 2
```

⚠️ **Y aquí hay una trampa de medición que casi me come.** Los contenedores de k3s **no los ve el
Docker de la máquina**: corren dentro de su propio containerd. Contarlos con `docker ps` daba `2`,
que son solo los de Nomad, y ese número parecía «los de los dos». Hay que contarlos donde viven.

> ⛔ La línea `nomad job status` no llegó a parsearse (fallo de mi `grep`, no de Nomad). La
> verificación de arriba es mejor de todos modos: cuenta los procesos reales, no lo que dice la
> herramienta de sí misma.

---

## 🥇 LA TABLA

| | Nomad | k3s | |
|---|---|---|---|
| líneas de configuración | **19** | 23 | casi empatan |
| tamaño de la imagen | **207 MB** | 297 MB | 1,4× |
| de cero a servicio listo | **13 s** | 16 s | **casi empatan** |
| memoria del plano de control | **157 MB** | 672 MB | **4,3× menos** |
| procesos vivos dentro | **2** | 9 | 4,5× menos |
| pods del sistema que levanta solo | 0 | **4** | |

## 🥇 DOS TÓPICOS QUE LA MEDICIÓN DESMIENTE

**1. «El YAML de Kubernetes es enorme».** Para el mismo servicio: **23 líneas contra 19**. Cuatro
de diferencia. El YAML no es el problema, y montar el vídeo sobre eso sería tumbado en los
comentarios en diez minutos.

**2. «Kubernetes tarda una eternidad en arrancar».** **16 segundos contra 13.** Con k3s, de nada a
un servicio con dos réplicas respondiendo. Prácticamente empatan.

## 🥇 DÓNDE ESTÁ LA DIFERENCIA DE VERDAD

No está en las líneas ni en el arranque: está en **lo que tienes que tener vivo**.

```
   procesos dentro del contenedor de Nomad: 2
   procesos dentro del contenedor de k3s:   9

   piezas de k3s que se ven por nombre:
     containerd · containerd-shim · coredns · exe · k3s
     local-path-prov · nginx · pause · ps

   pods del sistema que k3s levanta solo: 4
```

Nomad son **dos procesos**. k3s son nueve, y encima levanta **cuatro pods del sistema** que nadie
le pidió: el servidor de nombres del clúster, el aprovisionador de discos locales y compañía.

Y eso se traduce directamente en la memoria: **157 MB contra 672**.

⚠️ **Honestidad sobre la memoria:** entre dos corridas dio 101/524 MB y 157/672 MB. El número
absoluto se mueve; **la proporción no** (entre 4,3× y 5,2×). En el vídeo se da la proporción, no
el número exacto, y se dice que se movió.

---

## ⛔ Lo que NO mide este banco, y pesa mucho

**El ecosistema, que es donde Kubernetes gana y no es un detalle.** Todo lo que te encuentras ya
hecho —operadores, gráficos de Helm, controladores de entrada, la documentación de cualquier
proveedor de nube— asume Kubernetes. Con Nomad escribes tú lo que allí ya está escrito. Eso no sale
en ninguna tabla y decide más despliegues que los 500 MB de memoria.

Tampoco se mide: alta disponibilidad real (varios maestros), políticas de red, ni qué pasa a los
seis meses cuando entra gente nueva al equipo.

## Tropiezos reales — **cuatro, y todos daban números plausibles**

Ninguno tenía que ver con Nomad ni con Kubernetes. Todos producían resultados creíbles y falsos:

1. **El bucle de espera de Nomad** buscaba una cadena que su salida no tiene → medía su propio
   tiempo agotado. Daba **337 s** en vez de 13.
2. **El de k3s llamaba `k3s kubectl`**, que en esa imagen no existe (es `kubectl` a secas) → el
   despliegue **nunca se aplicó** y también medía el timeout. Y el error iba a `/dev/null`.
3. **Los contenedores que levanta Nomad no son hijos suyos para Docker**: sobrevivían al borrar el
   agente y se sumaban al recuento de la corrida siguiente.
4. **Los contenedores de k3s viven en su propio containerd** y `docker ps` no los ve: el recuento
   decía «2 nginx vivos» y eran solo los de Nomad.

Y uno más, de arranque, que **sí va en el vídeo pero como tropiezo, no como diferencia**: Nomad
muere al segundo dentro de un contenedor con
`failed to create nomad cgroup: device or resource busy`. Es la regla de cgroups v2 —un grupo no
puede tener procesos y delegar controladores a la vez— y se cura moviendo el proceso a un subgrupo
antes de arrancar (ver `arranca-nomad.sh`). No dice nada de Nomad contra Kubernetes.
