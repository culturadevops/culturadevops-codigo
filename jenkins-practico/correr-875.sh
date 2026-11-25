#!/bin/bash
# Banco del vídeo 875 «Jenkins como código (JCasC)». Desde Git Bash:
#   bash canales/cultura-devops/recursos/jenkins-practico/correr-875.sh   → escribe SALIDA-875.md
# Todo Jenkins sale de 875/jenkins.yaml (usuarios, permisos, credenciales, nube de agentes y jobs con Job DSL).
# Se monta una COPIA (875/_vivo) para poder editarla en la demo de recarga sin tocar el original.
cd "$(dirname "$0")" || exit 1
. ./comun.sh
N=${N:-5}
ENVF="$AQUI_WIN\\875\\secretos.env"
SOCK=(--group-add 0 -v /var/run/docker.sock:/var/run/docker.sock)

nuevo_jenkins() { parar_jenkins; arrancar_jenkins 875/_vivo --env-file "$ENVF" "${SOCK[@]}"; ARR=$(espera_jenkins); cli_jar; }
huella() { CLI groovy = < 875/estado.groovy; }
CLID() { docker exec -i $JK java -jar /tmp/jenkins-cli.jar -s http://jk-a-jenkins:8080/ -webSocket -auth dev:dev-de-prueba "$@" 2>&1 | tr -d '\r'; }
codigo() { docker exec $JK curl -s -o /dev/null -w '%{http_code}' -u "$1" "${@:2}"; }

banco() {
echo "### 0 · La imagen: versión de Jenkins y plugins fijados"
echo "\$ cat Dockerfile | grep -v '^#'"
grep -v '^#' Dockerfile
echo "\$ head -4 plugins.txt ; wc -l plugins.txt"
head -4 plugins.txt; echo "$(wc -l < plugins.txt) plugins.txt"
echo "\$ grep -E '^(configuration-as-code|job-dsl|matrix-auth|docker-plugin):' plugins.txt"
grep -E '^(configuration-as-code|job-dsl|matrix-auth|docker-plugin):' plugins.txt
echo "\$ jenkins --version"
docker exec $JK sh -c 'java -jar /usr/share/jenkins/jenkins.war --version'

echo
echo "### 1 · Arranque: docker run sin volumen, con jenkins.yaml montado y los secretos como variables"
echo "\$ docker run -d --rm --name jk-a-jenkins --env-file secretos.env -v ./875:/var/jenkins_home/casc:ro jk-a-jenkins:1"
echo "(listo en $ARR ms; sin asistente de instalación)"
echo "\$ jenkins groovy = < estado.groovy"
huella | tee ./_huella1

echo
echo "### 2 · Permisos de la matriz"
echo "admin  GET  /manage/                    → $(codigo admin:$ADMIN_PASS http://localhost:8080/manage/)"
echo "dev    GET  /manage/                    → $(codigo dev:dev-de-prueba http://localhost:8080/manage/)"
echo "dev    GET  /job/desplegar/configure    → $(codigo dev:dev-de-prueba http://localhost:8080/job/desplegar/configure)"
echo "\$ jenkins -auth dev:... build desplegar -s   # dev sí puede lanzar"
CLID build desplegar -s | tail -1
echo "\$ jenkins -auth dev:... get-job desplegar   # pero no leer la configuración"
CLID get-job desplegar | grep -m1 -E "ERROR|permission|Permission"
echo "nadie  GET  /job/desplegar/             → $(docker exec $JK curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/job/desplegar/)"

echo
echo "### 3 · El job usa las credenciales del YAML (Jenkins las enmascara)"
CLI build desplegar -s >/dev/null
echo "\$ jenkins console desplegar   (último build, líneas útiles)"
API http://localhost:8080/job/desplegar/lastBuild/consoleText | grep -E "^Started|usuario:|Finished|efimero" | grep -v '^+ '

echo
echo "### 4 · Exportar lo que hay (para empezar desde un Jenkins hecho a mano)"
echo "\$ jenkins export-configuration > exportado.yaml"
CLI export-configuration > ./_export1.yaml
echo "$(wc -l < ./_export1.yaml) líneas exportadas"
echo "\$ grep -A6 'usernamePassword' exportado.yaml"
grep -A6 'usernamePassword' ./_export1.yaml | sed -E 's/(\{AQAA.{20})[^}]*\}/\1...}/'

echo
echo "### 5 · Borrar el contenedor y crear otro desde el mismo YAML"
echo "\$ docker rm -f jk-a-jenkins ; docker run ... (lo mismo)"
nuevo_jenkins
echo "(listo en $ARR ms)"
huella > ./_huella2
cat ./_huella2
echo "\$ diff huella-antes huella-después"
diff ./_huella1 ./_huella2; echo "(diff: $(diff ./_huella1 ./_huella2 | grep -c '^[<>]') líneas con < o >)"
CLI export-configuration > ./_export2.yaml
echo "\$ diff exportado-antes.yaml exportado-después.yaml"
diff ./_export1.yaml ./_export2.yaml | sed -E 's/(\{AQAA.{20})[^}]*\}/\1...}/' | head -8
echo "(líneas distintas: $(diff ./_export1.yaml ./_export2.yaml | grep -c '^[<>]'))"
echo "# los valores {AQAA...} son los secretos cifrados con la llave de CADA Jenkins (secrets/ en jenkins_home): cambian en cada contenedor"
echo "\$ diff <(sed 's/{AQAA[^}]*}/<cifrado>/' antes) <(sed ... después)"
diff <(sed -E 's/\{AQAA[^}]*\}/<cifrado>/' ./_export1.yaml) <(sed -E 's/\{AQAA[^}]*\}/<cifrado>/' ./_export2.yaml) >/dev/null && echo "(idénticos)" || echo "(distintos)"

echo
echo "### 6 · Cambiar el YAML y recargar SIN reiniciar"
python - <<'PY'
p = '875/_vivo/jenkins.yaml'
s = open(p, encoding='utf-8').read()
s = s.replace("      pipelineJob('desplegar') {", "      pipelineJob('pruebas') {\n        definition { cps { sandbox(true); script(\"pipeline { agent { label 'efimero' }; stages { stage('Test') { steps { echo 'ok' } } } }\") } }\n      }\n      pipelineJob('desplegar') {")
s = s.replace('systemMessage: "Jenkins configurado con JCasC: no lo toques a mano"', 'systemMessage: "Jenkins configurado con JCasC (v2): no lo toques a mano"')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
PY
echo "(en jenkins.yaml: un pipelineJob('pruebas') más y el mensaje pasa a «(v2)»)"
echo "\$ jenkins reload-jcasc-configuration"
T0=$(ms); CLI reload-jcasc-configuration; echo "(recarga: $(( $(ms) - T0 )) ms)"
echo "\$ jenkins list-jobs"
CLI list-jobs
echo "mensaje: $(API http://localhost:8080/api/json?tree=description | python -c "import sys,json;print(json.load(sys.stdin)['description'])")"

echo
echo "### 7 · Un error de escritura en el YAML"
sed -i 's/^  numExecutors: 0/  numExecutor: 0/' 875/_vivo/jenkins.yaml
echo "(en jenkins.yaml: numExecutors → numExecutor)"
echo "\$ jenkins reload-jcasc-configuration"
CLI reload-jcasc-configuration | grep -vE '^\s+at ' | head -4
echo "\$ jenkins list-jobs   # el Jenkins que ya corría sigue igual"
CLI list-jobs
echo
echo "\$ docker rm -f jk-a-jenkins ; docker run ...   # arrancar desde cero con el YAML roto"
parar_jenkins; arrancar_jenkins 875/_vivo --env-file "$ENVF" "${SOCK[@]}"
sleep 60
echo "GET /login → $(docker exec $JK curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/login)  (60 s después)"
echo "\$ docker logs jk-a-jenkins | grep -m1 numExecutor"
docker logs $JK 2>&1 | grep -m1 -E "numExecutor" | sed -E 's/^.*(io\.jenkins|Invalid|Caused)/\1/' | cut -c1-220
cp 875/jenkins.yaml 875/_vivo/jenkins.yaml

echo
echo "### 8 · Cuánto tarda en volver: $N arranques desde cero (docker run → /login 200)"
candado
: > ./_arr
for i in $(seq 1 $N); do nuevo_jenkins; echo "$ARR" >> ./_arr; done
soltar_candado
echo "  arranques (ms): $(tr '\n' ' ' < ./_arr)"
echo "  mediana: $(mediana < ./_arr) ms"
CLI list-jobs | tr '\n' ' '; echo " ← jobs en el último arranque"
rm -f ./_arr ./_huella1 ./_huella2 ./_export1.yaml ./_export2.yaml
}

limpiar
construir_imagen
red
rm -rf 875/_vivo; mkdir -p 875/_vivo; cp 875/jenkins.yaml 875/_vivo/jenkins.yaml
nuevo_jenkins
{
  echo "# SALIDA 875 — Jenkins como código, JCasC (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). jk-a-jenkins:1 = jenkins/jenkins:2.580.2-lts-jdk21 + plugins.txt. Configuración: 875/jenkins.yaml; secretos de prueba en 875/secretos.env."
  echo
  echo '```'
  banco
  echo '```'
} > SALIDA-875.md 2>&1
limpiar
rm -rf 875/_vivo
cat SALIDA-875.md
