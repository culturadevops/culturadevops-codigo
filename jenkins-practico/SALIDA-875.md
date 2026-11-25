# SALIDA 875 — Jenkins como código, JCasC (cultura-devops)

> Corrida del 2026-11-18 11:47. jk-a-jenkins:1 = jenkins/jenkins:2.580.2-lts-jdk21 + plugins.txt. Configuración: 875/jenkins.yaml; secretos de prueba en 875/secretos.env.

```
### 0 · La imagen: versión de Jenkins y plugins fijados
$ cat Dockerfile | grep -v '^#'
FROM jenkins/jenkins:2.580.2-lts-jdk21
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc/jenkins.yaml
$ head -4 plugins.txt ; wc -l plugins.txt
antisamy-markup-formatter:173.v680e3a_b_69ff3
apache-httpcomponents-client-4-api:4.5.14-269.vfa_2321039a_83
apache-httpcomponents-client-5-api:5.6.5-209.vd1010d57ee17
asm-api:9.11.1-226.vff833a_e4c58e
76 plugins.txt
$ grep -E '^(configuration-as-code|job-dsl|matrix-auth|docker-plugin):' plugins.txt
configuration-as-code:2147.v8a_8d38668c72
docker-plugin:1337.v3ca_fd1b_b_25ef
job-dsl:3752.vb_199526b_20c3
matrix-auth:3.3
$ jenkins --version
2.580.2

### 1 · Arranque: docker run sin volumen, con jenkins.yaml montado y los secretos como variables
$ docker run -d --rm --name jk-a-jenkins --env-file secretos.env -v ./875:/var/jenkins_home/casc:ro jk-a-jenkins:1
(listo en 4964 ms; sin asistente de instalación)
$ jenkins groovy = < estado.groovy
mensaje:      Jenkins configurado con JCasC: no lo toques a mano
ejecutores:   0 en el controlador
usuarios:     admin, dev
seguridad:    HudsonPrivateSecurityRealm + GlobalMatrixAuthorizationStrategy
credenciales: registro (UsernamePasswordCredentialsImpl), token-api (StringCredentialsImpl)
nubes:        docker: efimero = jenkins/agent:3395.v6e5377b_0fb_3c-5-jdk21
job:          desplegar · config.xml md5 adc42597d73a · último build: ninguno

### 2 · Permisos de la matriz
admin  GET  /manage/                    → 200
dev    GET  /manage/                    → 403
dev    GET  /job/desplegar/configure    → 403
$ jenkins -auth dev:... build desplegar -s   # dev sí puede lanzar
ERROR: dev is missing the Job/Cancel permission
$ jenkins -auth dev:... get-job desplegar   # pero no leer la configuración
ERROR: dev is missing the Job/Configure permission
nadie  GET  /job/desplegar/             → 403

### 3 · El job usa las credenciales del YAML (Jenkins las enmascara)
$ jenkins console desplegar   (último build, líneas útiles)
Started from command line by admin
Running on efimero-00003b6bhvhqi on docker in /home/jenkins/agent/workspace/desplegar
usuario: ci-bot · clave: **** · token: ****
Finished: SUCCESS

### 4 · Exportar lo que hay (para empezar desde un Jenkins hecho a mano)
$ jenkins export-configuration > exportado.yaml
246 líneas exportadas
$ grep -A6 'usernamePassword' exportado.yaml
      - usernamePassword:
          description: "Usuario del registro de imágenes"
          id: "registro"
          password: "{AQAAABAAAAAgNpZlRRGgj29M...}"
          scope: GLOBAL
          username: "ci-bot"
      - string:

### 5 · Borrar el contenedor y crear otro desde el mismo YAML
$ docker rm -f jk-a-jenkins ; docker run ... (lo mismo)
(listo en 4879 ms)
mensaje:      Jenkins configurado con JCasC: no lo toques a mano
ejecutores:   0 en el controlador
usuarios:     admin, dev
seguridad:    HudsonPrivateSecurityRealm + GlobalMatrixAuthorizationStrategy
credenciales: registro (UsernamePasswordCredentialsImpl), token-api (StringCredentialsImpl)
nubes:        docker: efimero = jenkins/agent:3395.v6e5377b_0fb_3c-5-jdk21
job:          desplegar · config.xml md5 adc42597d73a · último build: ninguno
$ diff huella-antes huella-después
(diff: 0 líneas con < o >)
$ diff exportado-antes.yaml exportado-después.yaml
17c17
<           password: "{AQAAABAAAAAgNpZlRRGgj29M...}"
---
>           password: "{AQAAABAAAAAgPg0p3ScJrK/r...}"
24c24
<           secret: "{AQAAABAAAAAgiYCmxnyn37CY...}"
---
>           secret: "{AQAAABAAAAAgtOaCAxdhyfGy...}"
(líneas distintas: 4)
# los valores {AQAA...} son los secretos cifrados con la llave de CADA Jenkins (secrets/ en jenkins_home): cambian en cada contenedor
$ diff <(sed 's/{AQAA[^}]*}/<cifrado>/' antes) <(sed ... después)
(idénticos)

### 6 · Cambiar el YAML y recargar SIN reiniciar
(en jenkins.yaml: un pipelineJob('pruebas') más y el mensaje pasa a «(v2)»)
$ jenkins reload-jcasc-configuration
(recarga: 1148 ms)
$ jenkins list-jobs
desplegar
pruebas
mensaje: Jenkins configurado con JCasC (v2): no lo toques a mano

### 7 · Un error de escritura en el YAML
(en jenkins.yaml: numExecutors → numExecutor)
$ jenkins reload-jcasc-configuration

ERROR: Unexpected exception occurred while performing reload-jcasc-configuration command.
io.jenkins.plugins.casc.UnknownAttributesException: jenkins: Invalid configuration elements for type: class jenkins.model.Jenkins : numExecutor.
Available attributes : authorizationStrategy, clouds, crumbIssuer, disableRememberMe, disabledAdministrativeMonitors, globalNodeProperties, labelAtoms, labelString, log, markupFormatter, mode, noUsageStatistics, nodeMonitors, nodeName, nodeProperties, nodes, numExecutors, primaryView, projectNamingStrategy, proxy, quietPeriod, remotingSecurity, scmCheckoutRetryCount, securityRealm, slaveAgentPort, systemMessage, updateCenter, views, viewsTabBar
$ jenkins list-jobs   # el Jenkins que ya corría sigue igual
desplegar
pruebas

$ docker rm -f jk-a-jenkins ; docker run ...   # arrancar desde cero con el YAML roto
Error response from daemon: No such container: jk-a-jenkins
GET /login →   (60 s después)
$ docker logs jk-a-jenkins | grep -m1 numExecutor

### 8 · Cuánto tarda en volver: 5 arranques desde cero (docker run → /login 200)
  arranques (ms): 5176 4662 4682 4641 4735 
  mediana: 4682 ms
desplegar  ← jobs en el último arranque
```
