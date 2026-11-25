#!/usr/bin/env bash
# Demo del vídeo 482 «¿Vale la pena aprender Jenkins en la era de la IA?» — se EJECUTA y su salida va a SALIDA.md.
# Un Jenkins LTS de verdad en Docker (solo en esta máquina, sin exponerse fuera de localhost), con los plugins de Pipeline.
#   1) un Jenkinsfile típico de lo que genera una IA, con directivas que no existen: el validador de Jenkins lo rechaza;
#   2) el revisado pasa el validador;  3) se crea el trabajo y se ejecuta: «Finished: SUCCESS».
# Al final el contenedor se borra.
set -u
export MSYS_NO_PATHCONV=1
export PYTHONUTF8=1
T=$(mktemp -d)
cd "$T"
N=demo482-jenkins
P=18482
J="http://127.0.0.1:$P"

cat > Dockerfile <<'EOF'
FROM jenkins/jenkins:2.580.1-lts-jdk21
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
RUN jenkins-plugin-cli --plugins workflow-aggregator pipeline-model-definition
EOF
docker rm -f "$N" >/dev/null 2>&1
docker build -q -t demo482 "$(cygpath -w "$T")" >/dev/null 2>&1
docker run -d --name "$N" -p 127.0.0.1:$P:8080 demo482 >/dev/null
for i in $(seq 1 90); do curl -s -o /dev/null -w "%{http_code}" "$J/api/json" | grep -q 200 && break; sleep 2; done

COOK=cookies
CR=$(curl -s -c "$COOK" "$J/crumbIssuer/api/json" | python -c "import sys,json; d=json.load(sys.stdin); print(d['crumbRequestField']+':'+d['crumb'])")
validar() { curl -s -b "$COOK" -H "$CR" -X POST -F "jenkinsfile=<$1" "$J/pipeline-model-converter/validate"; echo; }

cat > Jenkinsfile.ia <<'EOF'
pipeline {
    agent any
    options {
        retryOnFailure(3)
    }
    stages {
        stage('Test') {
            steps {
                sh 'python3 -m pytest'
            }
        }
        stage('Deploy') {
            when { branch 'main' }
            runOn 'produccion'
            steps {
                sh './deploy.sh'
            }
        }
    }
}
EOF

cat > Jenkinsfile <<'EOF'
pipeline {
    agent any
    options {
        timeout(time: 10, unit: 'MINUTES')
    }
    stages {
        stage('Test') {
            steps {
                retry(3) {
                    sh 'echo "pruebas: 12 pasaron"'
                }
            }
        }
        stage('Build') {
            steps {
                sh 'echo "versión $BUILD_NUMBER lista" > version.txt && cat version.txt'
            }
        }
    }
}
EOF

echo '$ curl -s localhost:8080/api/json | grep version   # Jenkins en Docker, solo local'
curl -s -I "$J/api/json" | grep -i "^x-jenkins:" | tr -d '\r'
echo
echo '$ cat Jenkinsfile   # típico de lo que genera una IA'
cat Jenkinsfile.ia
echo '$ curl -X POST -F "jenkinsfile=<Jenkinsfile" localhost:8080/pipeline-model-converter/validate'
validar Jenkinsfile.ia
echo
echo '$ # versión revisada: «retryOnFailure» no existe (la opción se llama retry) y «runOn» tampoco'
echo '$ curl -X POST -F "jenkinsfile=<Jenkinsfile" localhost:8080/pipeline-model-converter/validate'
validar Jenkinsfile
echo
python - "$(cygpath -w "$T/Jenkinsfile")" > config.xml <<'PY'
import sys, html
print("<?xml version='1.1' encoding='UTF-8'?><flow-definition plugin='workflow-job'><definition class='org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition' plugin='workflow-cps'><script>"
      + html.escape(open(sys.argv[1], encoding='utf-8').read()) + "</script><sandbox>true</sandbox></definition></flow-definition>")
PY
curl -s -b "$COOK" -H "$CR" -H "Content-Type: application/xml" --data-binary @config.xml "$J/createItem?name=demo" -o /dev/null
curl -s -b "$COOK" -H "$CR" -X POST "$J/job/demo/build" -o /dev/null
for i in $(seq 1 60); do curl -s "$J/job/demo/1/api/json" 2>/dev/null | grep -q '"building":false' && break; sleep 2; done
echo '$ # se crea el trabajo «demo» con el Jenkinsfile revisado y se ejecuta'
echo '$ curl localhost:8080/job/demo/1/consoleText'
curl -s "$J/job/demo/1/consoleText" | grep -vE "^\[Pipeline\] (\{|\}|// |node|stage|withEnv|timeout|retry|sh|End of Pipeline|Start of Pipeline)|^Running on|^Started by|^Running in Durability|^Running as SYSTEM|^Timeout set" | grep -v "^$"
docker rm -f "$N" >/dev/null 2>&1
docker rmi demo482 >/dev/null 2>&1
cd / && rm -rf "$T"
