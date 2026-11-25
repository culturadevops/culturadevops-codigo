# SALIDA-877-gracia · cuánto tarda en irse el pod-agente

> Corrida 2026-11-18 15:46 UTC. `k8s/correr_877_gracia.py`, candado tomado. En caliente (imágenes ya en el nodo). Alternando las dos variantes.
- pod-agente 1: build #11 · espera 3.5 s · pod borrado 30.4 s después del build
- gracia 1: build #1 · espera 2.8 s · pod borrado 3.5 s después del build
- pod-agente 2: build #12 · espera 3.0 s · pod borrado 29.8 s después del build
- gracia 2: build #2 · espera 3.1 s · pod borrado 3.5 s después del build
- pod-agente 3: build #13 · espera 2.4 s · pod borrado 29.9 s después del build
- gracia 3: build #3 · espera 3.2 s · pod borrado 2.9 s después del build
- pod-agente 4: build #14 · espera 2.8 s · pod borrado 29.5 s después del build
- gracia 4: build #4 · espera 2.9 s · pod borrado 3.5 s después del build
- pod-agente 5: build #15 · espera 3.1 s · pod borrado 30.5 s después del build
- gracia 5: build #5 · espera 2.6 s · pod borrado 3.5 s después del build

- al acabar: No resources found in jenkins-agentes namespace.
- **por defecto (gracia 30 s)**: el pod se va 29.9 s después del build (mediana de 5: 30.4, 29.8, 29.9, 29.5, 30.5) · espera de arranque mediana 3.0 s
- **terminationGracePeriodSeconds: 3**: el pod se va 3.5 s después del build (mediana de 5: 3.5, 3.5, 2.9, 3.5, 3.5) · espera de arranque mediana 2.9 s
