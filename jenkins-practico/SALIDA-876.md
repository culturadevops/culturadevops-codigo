# SALIDA 876 — Jenkins Shared Libraries (cultura-devops)

> Corrida del 2026-11-18 11:53. jk-a-jenkins:1 = jenkins/jenkins:2.580.2-lts-jdk21 + plugins.txt; librería y jobs en 876/jenkins.yaml. Servidor git: jk-a-git:1 = alpine:3.22 + git-daemon. Los builds corren en el controlador (2 ejecutores) para no mezclar agentes en este vídeo.

```
### 0 · Versiones
2.580.2
configuration-as-code 2147.v8a_8d38668c72
git 5.11.0
pipeline-groovy-lib 822.vc95f70dea_db_7
git (servidor) git version 2.49.1

### 1 · La librería y un Jenkinsfile
jk-a-git$ git -C pipeline-comun ls-tree -r --name-only v1.0
vars/avisar.groovy
vars/empaquetar.groovy
vars/pipelineEstandar.groovy
jk-a-git$ wc -l vars/*.groovy
        4 vars/avisar.groovy
        6 vars/empaquetar.groovy
       20 vars/pipelineEstandar.groovy
       30 total
jk-a-git$ cat tienda-web/Jenkinsfile ; wc -l
@Library('pipeline-comun@v1.0') _

pipelineEstandar(nombre: 'tienda-web')
3
jk-a-git$ wc -l tienda-web/Jenkinsfile.completo   # el mismo pipeline sin librería
21
jk-a-git$ head -1 */Jenkinsfile
tienda-web: @Library('pipeline-comun@v1.0') _
api-pagos: @Library('pipeline-comun@v1.0') _
worker-correos: @Library('pipeline-comun') _

### 2 · Primera vuelta: los tres proyectos con la librería tal cual
--- tienda-web #1
Loading library pipeline-comun@v1.0
Attempting to resolve v1.0 from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Compilar
compilando tienda-web
  etapa: Pruebas
tienda-web: 12 pruebas, 0 fallos
  etapa: Empaquetar
paquete: tienda-web-1.tgz
  etapa: Declarative: Post Actions
[aviso] tienda-web #1: SUCCESS
Finished: SUCCESS
--- api-pagos #1
Loading library pipeline-comun@v1.0
Attempting to resolve v1.0 from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Compilar
compilando api-pagos
  etapa: Pruebas
api-pagos: 12 pruebas, 0 fallos
  etapa: Empaquetar
paquete: api-pagos-1.tgz
  etapa: Declarative: Post Actions
[aviso] api-pagos #1: SUCCESS
Finished: SUCCESS
--- worker-correos #1
Loading library pipeline-comun@main
Attempting to resolve main from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Compilar
compilando worker-correos
  etapa: Pruebas
worker-correos: 12 pruebas, 0 fallos
  etapa: Empaquetar
paquete: worker-correos-1.tgz
  etapa: Declarative: Post Actions
[aviso] worker-correos #1: SUCCESS
Finished: SUCCESS

### 3 · Alguien cambia la librería en main (sin etiqueta nueva)
jk-a-git$ git diff --stat ; git diff (resumen)
 vars/pipelineEstandar.groovy | 3 +++
 1 file changed, 3 insertions(+)
+      stage('Buscar secretos') {
+        steps { sh '! grep -rnI --exclude-dir=.git "password=" .' }
+      }
<commit> (HEAD -> main, origin/main) añade la etapa Buscar secretos
<commit> (tag: v1.0) primera versión
--- tienda-web #2   (@Library('pipeline-comun@v1.0') _)
Loading library pipeline-comun@v1.0
Attempting to resolve v1.0 from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Compilar
compilando tienda-web
  etapa: Pruebas
tienda-web: 12 pruebas, 0 fallos
  etapa: Empaquetar
paquete: tienda-web-2.tgz
  etapa: Declarative: Post Actions
[aviso] tienda-web #2: SUCCESS
Finished: SUCCESS
--- api-pagos #2   (@Library('pipeline-comun@v1.0') _)
Loading library pipeline-comun@v1.0
Attempting to resolve v1.0 from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Compilar
compilando api-pagos
  etapa: Pruebas
api-pagos: 12 pruebas, 0 fallos
  etapa: Empaquetar
paquete: api-pagos-2.tgz
  etapa: Declarative: Post Actions
[aviso] api-pagos #2: SUCCESS
Finished: SUCCESS
--- worker-correos #2   (@Library('pipeline-comun') _)
Loading library pipeline-comun@main
Attempting to resolve main from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Buscar secretos
./config/smtp.properties:3:smtp.password=hunter2
  etapa: Compilar
  etapa: Pruebas
  etapa: Empaquetar
  etapa: Declarative: Post Actions
[aviso] worker-correos #2: FAILURE
ERROR: script returned exit code 1
Finished: FAILURE

### 4 · Se publica v2.0 y un proyecto decide subir
v1.0
v2.0
@Library('pipeline-comun@v2.0') _
--- api-pagos #3
Loading library pipeline-comun@v2.0
Attempting to resolve v2.0 from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Buscar secretos
  etapa: Compilar
compilando api-pagos
  etapa: Pruebas
api-pagos: 12 pruebas, 0 fallos
  etapa: Empaquetar
paquete: api-pagos-3.tgz
  etapa: Declarative: Post Actions
[aviso] api-pagos #3: SUCCESS
Finished: SUCCESS
--- tienda-web #3 (sigue en v1.0)
Loading library pipeline-comun@v1.0
Attempting to resolve v1.0 from remote references...
  etapa: Declarative: Checkout SCM
  etapa: Compilar
compilando tienda-web
  etapa: Pruebas
tienda-web: 12 pruebas, 0 fallos
  etapa: Empaquetar
paquete: tienda-web-3.tgz
  etapa: Declarative: Post Actions
[aviso] tienda-web #3: SUCCESS
Finished: SUCCESS

### 5 · ¿Cuánto cuesta cargar la librería? 7 builds de cada uno (duración según la API)
  tienda-web: 1694 1706 1711 1684 1664 1717 1695 → mediana 1695 ms
  tienda-web-sin-libreria: 1480 1386 1372 1378 1357 1389 1350 → mediana 1378 ms
```
