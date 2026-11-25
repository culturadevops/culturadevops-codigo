#!/bin/bash
# Banco del vídeo 876 «Jenkins Shared Libraries». Desde Git Bash:
#   bash canales/cultura-devops/recursos/jenkins-practico/correr-876.sh   → escribe SALIDA-876.md
# jk-a-git: un servidor git (git daemon) con la librería pipeline-comun y tres proyectos.
# jk-a-jenkins: la librería se declara en 876/jenkins.yaml y los jobs salen de Job DSL.
cd "$(dirname "$0")" || exit 1
. ./comun.sh
N=${N:-7}
GIT_IMG=jk-a-git:1
G() { docker exec jk-a-git sh -c "$*" 2>&1 | tr -d '\r'; }
GITC="git -c user.name=equipo-plataforma -c user.email=plataforma@ejemplo.test -c init.defaultBranch=main"

# repo_nuevo <nombre> <carpeta local>: crea el repo desnudo, sube la carpeta como primer commit en main
repo_nuevo() {
  docker cp "$2/." jk-a-git:/tmp/src-$1 >/dev/null
  G "git init -q --bare -b main /srv/git/$1.git && $GITC clone -q /srv/git/$1.git /work/$1 2>/dev/null; cp -r /tmp/src-$1/. /work/$1/ && cd /work/$1 && chmod +x *.sh 2>/dev/null; $GITC add -A && $GITC commit -qm 'primera versión' && $GITC push -q origin main"
}

consola() {  # job [build] → solo las líneas que cuentan la historia
  API "http://localhost:8080/job/$1/${2:-lastBuild}/consoleText" | grep -E "Loading library|Attempting to resolve|^\[Pipeline\] \{ \(|^compilando|pruebas,|^paquete:|^\[aviso\]|^Finished|password|^ERROR|script returned" \
    | grep -v '^+ ' | sed -E 's/[0-9a-f]{40}/<commit>/g; s/^\[Pipeline\] \{ \((.*)\)/  etapa: \1/'
}

banco() {
echo "### 0 · Versiones"
docker exec $JK sh -c 'java -jar /usr/share/jenkins/jenkins.war --version'
CLI list-plugins | grep -E "^(pipeline-groovy-lib|git|configuration-as-code) " | awk '{print $1, $NF}'
echo "git (servidor) $(G git --version)"

echo
echo "### 1 · La librería y un Jenkinsfile"
echo "jk-a-git\$ git -C pipeline-comun ls-tree -r --name-only v1.0"
G "cd /work/pipeline-comun && git ls-tree -r --name-only v1.0"
echo "jk-a-git\$ wc -l vars/*.groovy"
G "cd /work/pipeline-comun && wc -l vars/*.groovy"
echo "jk-a-git\$ cat tienda-web/Jenkinsfile ; wc -l"
G "cat /work/tienda-web/Jenkinsfile; wc -l < /work/tienda-web/Jenkinsfile"
echo "jk-a-git\$ wc -l tienda-web/Jenkinsfile.completo   # el mismo pipeline sin librería"
G "wc -l < /work/tienda-web/Jenkinsfile.completo"
echo "jk-a-git\$ head -1 */Jenkinsfile"
G "cd /work && for p in tienda-web api-pagos worker-correos; do echo \"\$p: \$(head -1 \$p/Jenkinsfile)\"; done"

echo
echo "### 2 · Primera vuelta: los tres proyectos con la librería tal cual"
for p in tienda-web api-pagos worker-correos; do
  CLI build $p -s >/dev/null
  echo "--- $p #1"; consola $p
done

echo
echo "### 3 · Alguien cambia la librería en main (sin etiqueta nueva)"
docker cp 876/libreria-v2/vars/pipelineEstandar.groovy jk-a-git:/work/pipeline-comun/vars/pipelineEstandar.groovy >/dev/null
echo "jk-a-git\$ git diff --stat ; git diff (resumen)"
G "cd /work/pipeline-comun && git diff --stat && git diff | grep '^[+-] ' "
G "cd /work/pipeline-comun && $GITC commit -qam 'añade la etapa Buscar secretos' && $GITC push -q origin main && git log --oneline --decorate | sed -E 's/^[0-9a-f]+/<commit>/'"
for p in tienda-web api-pagos worker-correos; do
  CLI build $p -s >/dev/null
  echo "--- $p #2   ($(G "head -1 /work/$p/Jenkinsfile"))"; consola $p
done

echo
echo "### 4 · Se publica v2.0 y un proyecto decide subir"
G "cd /work/pipeline-comun && $GITC tag -a v2.0 -m 'v2.0: etapa Buscar secretos' && $GITC push -q origin v2.0 && git tag"
G "cd /work/api-pagos && sed -i 's/@v1.0/@v2.0/' Jenkinsfile && $GITC commit -qam 'usa pipeline-comun v2.0' && $GITC push -q origin main && head -1 Jenkinsfile"
CLI build api-pagos -s >/dev/null
echo "--- api-pagos #3"; consola api-pagos
CLI build tienda-web -s >/dev/null
echo "--- tienda-web #3 (sigue en v1.0)"; consola tienda-web

echo
echo "### 5 · ¿Cuánto cuesta cargar la librería? $N builds de cada uno (duración según la API)"
candado
for j in tienda-web tienda-web-sin-libreria; do
  : > ./_d_$j
  for i in $(seq 1 $N); do
    CLI build $j -s >/dev/null
    API "http://localhost:8080/job/$j/lastBuild/api/json?tree=duration" | python -c "import sys,json;print(json.load(sys.stdin)['duration'])" >> ./_d_$j
  done
done
soltar_candado
for j in tienda-web tienda-web-sin-libreria; do
  echo "  $j: $(tr '\n' ' ' < ./_d_$j)→ mediana $(mediana < ./_d_$j) ms"
done
rm -f ./_d_tienda-web ./_d_tienda-web-sin-libreria
}

limpiar
construir_imagen
red
docker run -d --rm --name jk-a-git --hostname jk-a-git --network $RED --ulimit core=1 --entrypoint sh $GIT_IMG \
  -c 'mkdir -p /srv/git /work && exec git daemon --reuseaddr --base-path=/srv/git --export-all /srv/git' >/dev/null
sleep 1
repo_nuevo pipeline-comun 876/libreria
G "cd /work/pipeline-comun && $GITC tag -a v1.0 -m 'v1.0' && $GITC push -q origin v1.0"
for p in tienda-web api-pagos worker-correos; do repo_nuevo $p 876/proyectos/$p; done
arrancar_jenkins 876
ARR=$(espera_jenkins)
cli_jar
{
  echo "# SALIDA 876 — Jenkins Shared Libraries (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). jk-a-jenkins:1 = jenkins/jenkins:2.580.2-lts-jdk21 + plugins.txt; librería y jobs en 876/jenkins.yaml. Servidor git: $GIT_IMG = alpine:3.22 + git-daemon. Los builds corren en el controlador (2 ejecutores) para no mezclar agentes en este vídeo."
  echo
  echo '```'
  banco
  echo '```'
} > SALIDA-876.md 2>&1
limpiar
cat SALIDA-876.md
