#!/bin/bash
# Levanta «gitserver» y «jenkins», corre la demo y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-jenkins-error-fetching-remote-repo/ejecutar.sh
# Las contraseñas y llaves son de prueba y se borran con los contenedores.
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
RED=demo-jenkins-git
limpiar() { docker rm -f jenkins gitserver >/dev/null 2>&1; docker network rm $RED >/dev/null 2>&1; rm -f ./_job.xml ./_cred-ssh.xml ./_cred-ssh-mal.xml; }
limpiar
docker build -q -t demo-gitserver:1 gitserver >/dev/null && docker build -q -t demo-jenkins-git:1 jenkins >/dev/null || exit 1
docker network create $RED >/dev/null
docker run -d --name gitserver --hostname gitserver --network $RED demo-gitserver:1 >/dev/null
docker exec gitserver htpasswd -bc /etc/nginx/htpasswd jenkins token-de-prueba >/dev/null 2>&1
docker run -d --name jenkins --network $RED demo-jenkins-git:1 >/dev/null
# Espera a que Jenkins conteste y baja su CLI.
for i in $(seq 1 90); do docker exec jenkins curl -sf http://localhost:8080/login >/dev/null 2>&1 && break; sleep 2; done
docker exec jenkins curl -s -o /tmp/jenkins-cli.jar http://localhost:8080/jnlpJars/jenkins-cli.jar
# La llave SSH de Jenkins: la privada va a una credencial, la pública al usuario git del servidor.
docker exec jenkins sh -c "rm -f /tmp/k /tmp/k.pub; ssh-keygen -q -t ed25519 -N '' -C jenkins -f /tmp/k"
docker exec jenkins cat /tmp/k.pub | docker exec -i gitserver sh -c "cat >> /home/git/.ssh/authorized_keys && chown git:git /home/git/.ssh/authorized_keys && chmod 600 /home/git/.ssh/authorized_keys"
# La credencial XML: la llave tal cual (sin líneas de más), y una copia «mal pegada» con una línea en blanco delante.
cred_ssh() {  # $1 = prefijo antes de la llave
  printf '%s
' '<com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey>'     '  <scope>GLOBAL</scope><id>git-ssh</id><description>llave de Jenkins (demo)</description><username>git</username>'
  printf '%s' '  <privateKeySource class="com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey$DirectEntryPrivateKeySource"><privateKey>'
  printf '%b' "$1"
  docker exec jenkins cat /tmp/k
  printf '%s
' '</privateKey></privateKeySource>' '</com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey>'
}
cred_ssh "" > ./_cred-ssh.xml
cred_ssh "
" > ./_cred-ssh-mal.xml
{
  echo "# SALIDA — Jenkins: error fetching remote repo 'origin' (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). jenkins/jenkins:2.580.1-lts-jdk21 con el plugin de git; servidor git propio (alpine 3.22: git-http-backend + nginx, y sshd). Contraseñas y llaves de prueba."
  echo
  echo '```'
  bash ./correr.sh
  echo '```'
} > SALIDA.md
limpiar
cat SALIDA.md
