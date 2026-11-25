# SALIDA · banco jenkins-k8s-y-velocidad (cultura-devops 877 y 878)

Corridas del 2026-11-18. Cada cifra de los guiones sale de uno de estos archivos; ninguna de blogs ni de memoria.

| archivo | vídeo | qué es | cómo se repite |
|---|---|---|---|
| `SALIDA-877.md` | 877 | arranque frío (3) / caliente (5), tres builds a la vez, pod que no cabe, OOM | `k8s/crear_cluster.sh` · `k8s/levantar_877.sh` · `python k8s/correr_877.py` |
| `SALIDA-877-gracia.md` | 877 | cuánto tarda en irse el pod: gracia por defecto contra 3 s (5+5 alternadas) | `python k8s/correr_877_gracia.py` |
| `SALIDA-877-consola.md` | 877 | consola completa de un build y `kubectl get pods` cada medio segundo (sin cronómetro) | `python k8s/consola_877.py` |
| `SALIDA-878.md` | 878 | 6 variantes del pipeline de PetClinic, 4 rondas intercaladas, clone aislado, tamaños y la trampa del ensayo | `velocidad/preparar_repo.sh` · `docker build -f velocidad/Dockerfile.agente -t jk-b-agente-petclinic:1 velocidad` · `velocidad/levantar_878.sh` · `python velocidad/correr_878.py` |

## Piezas fijas
- Jenkins: `jenkins/Dockerfile` → `jk-b-jenkins:2.580.2` (jenkins/jenkins:2.580.2-lts-jdk21 + 73 plugins de `jenkins/plugins.txt` + cliente docker 29.6.2). Sin asistente; JCasC en `jenkins/casc-877.yaml` y `jenkins/casc-878.yaml`.
- 877: kind v0.30.0, `k8s/kind.yaml` (kindest/node v1.34.0@sha256:7416a61b…), red propia `jk-b-net` 10.211.50.0/24 (los rangos por defecto de Docker de esta máquina están agotados), RBAC en `k8s/rbac.yaml`, pipelines en `k8s/pipelines/`.
- 878: spring-petclinic (`velocidad/petclinic-origen.git`, clon bare del original) fijado en 500158f7 + un commit con `velocidad/jenkinsfiles/`, rama `banco`. Consolas de cada build en `velocidad/_consolas/` (corrida medida) y `velocidad/_consolas_prueba/` (ensayo).
- Candado: los scripts que cronometran toman `<proyecto>/_logs/banco.lock`. `con_candado.sh <cmd>` lo hace para cualquier comando.

## Cosas que salieron por el camino
- 877: abortar un build cuyo pod está Pending NO borra el pod (seguía a los 180 s; se borró con kubectl).
- 877: un contenedor OOMKilled termina el build en ABORTED, no en FAILURE (3 de 3).
- 878: con `--volumes-from`, el agente ve el socket de Docker del controlador y Testcontainers levantaba contenedores en la máquina (`DOCKER_HOST` no lo evita: cae al socket). Las dos pruebas con Docker se excluyen con `-Dtest` en todas las variantes.
- 878: el plugin junit no está entre los 73: los Jenkinsfile no publican informes; las pruebas se cuentan de los resúmenes de Surefire en la consola.
