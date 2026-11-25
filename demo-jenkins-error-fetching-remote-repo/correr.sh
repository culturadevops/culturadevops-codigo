#!/bin/bash
# Demo de «Jenkins: error fetching remote repo 'origin'» (cultura-devops, 2026-10-23). Lo llama ejecutar.sh.
# «jenkins» = Jenkins LTS con el plugin de git. «gitserver» = un servidor git propio (HTTP público, HTTP con contraseña y SSH).
# Cada caso parte de un trabajo que FUNCIONA y luego se rompe: así sale «fetching». En un trabajo nuevo el mismo error dice «cloning».
set -u
J() { docker exec jenkins "$@" 2>&1; }
G() { docker exec gitserver "$@" 2>&1; }
CLI() { docker exec -i jenkins java -jar /tmp/jenkins-cli.jar -s http://localhost:8080/ -webSocket "$@" 2>&1; }
trabajo() {  # nombre url [credencial]: un trabajo de estilo libre que solo hace checkout de esa URL
  local creds=""
  [ -n "${3:-}" ] && creds="<credentialsId>$3</credentialsId>"
  sed -e "s#__URL__#$2#" -e "s#__CREDS__#$creds#" job.xml.tpl > ./_job.xml
  if CLI get-job "$1" >/dev/null 2>&1; then CLI update-job "$1" < ./_job.xml >/dev/null; else CLI create-job "$1" < ./_job.xml >/dev/null; fi
}
construir() {  # lo construye y deja solo las líneas del log que importan
  echo "\$ jenkins build $1   (consola, solo las líneas que importan)"
  CLI build "$1" -s -v | tr -d '\r' \
    | grep -E "^Started [a-z]|git fetch|^ERROR|stderr:|^fatal:|Host key|Permission denied|Checking out Revision|^Finished" \
    | grep -v "Started from command line" | sed -E 's/[0-9a-f]{40}/<commit>/g; s/ # timeout=10//; s/^hudson.plugins.git.GitException: //; s/^Caused by: hudson.plugins.git.GitException: //' | awk '!(/^ERROR/ && seen[$0]++)' | head -10
}

echo "### 0 · Versiones"
echo "jenkins\$ jenkins --version ; git --version"
J sh -c "java -jar /usr/share/jenkins/jenkins.war --version; git --version"
echo "jenkins\$ jenkins list-plugins | grep '^git '"
CLI list-plugins | grep -E "^git " | awk '{print $1, $NF}'

echo
echo "### 1 · La URL: el repo cambió de nombre"
trabajo tienda "http://gitserver/git/tienda.git"
construir tienda
echo
echo "gitserver\$ mv /srv/git/tienda.git /srv/git/tienda-web.git   # alguien renombra el repo"
G mv /srv/git/tienda.git /srv/git/tienda-web.git
construir tienda
echo
echo "jenkins\$ git ls-remote http://gitserver/git/tienda.git   # el mismo error, fuera de Jenkins"
J git ls-remote http://gitserver/git/tienda.git
echo "jenkins\$ git ls-remote http://gitserver/git/tienda-web.git"
J git ls-remote http://gitserver/git/tienda-web.git | sed -E 's/[0-9a-f]{40}/<commit>/'
trabajo tienda "http://gitserver/git/tienda-web.git"
echo "(URL del trabajo corregida: http://gitserver/git/tienda-web.git)"
construir tienda

echo
echo "### 2 · Un trabajo NUEVO: el mismo error dice «cloning»"
trabajo tienda-nueva "http://gitserver/git/tieda.git"
echo "(URL con una letra de menos: tieda)"
construir tienda-nueva

echo
echo "### 3 · Repo privado: sin credenciales"
trabajo api "http://gitserver/git/privado/api.git"
construir api
echo
echo "jenkins\$ git ls-remote http://gitserver/git/privado/api.git"
J sh -c "GIT_TERMINAL_PROMPT=0 git ls-remote http://gitserver/git/privado/api.git"
echo "\$ jenkins create-credentials-by-xml system::system::jenkins _ < cred-http.xml   (usuario jenkins, id git-http)"
CLI create-credentials-by-xml system::system::jenkins _ < cred-http.xml
trabajo api "http://gitserver/git/privado/api.git" git-http
echo "(el trabajo ahora usa credentialsId git-http)"
construir api

echo
echo "### 4 · Repo privado: el token caducó"
echo "gitserver\$ htpasswd -b /etc/nginx/htpasswd jenkins token-nuevo   # el token viejo ya no vale"
G htpasswd -b /etc/nginx/htpasswd jenkins token-nuevo
construir api
echo
echo "\$ jenkins update-credentials-by-xml system::system::jenkins _ git-http < cred-http-nuevo.xml"
CLI update-credentials-by-xml system::system::jenkins _ git-http < cred-http-nuevo.xml
construir api

echo
echo "### 5 · Por SSH: la huella del servidor"
CLI create-credentials-by-xml system::system::jenkins _ < ./_cred-ssh.xml
trabajo api-ssh "git@gitserver:/srv/git/privado/api.git" git-ssh
echo "(credencial git-ssh: la llave privada de Jenkins; su llave pública ya está en el servidor)"
construir api-ssh
echo
echo "jenkins\$ ssh-keyscan -t ed25519 gitserver >> ~/.ssh/known_hosts"
J sh -c "mkdir -p ~/.ssh && ssh-keyscan -t ed25519 gitserver 2>/dev/null >> ~/.ssh/known_hosts && cut -c1-60 ~/.ssh/known_hosts"
construir api-ssh

echo
echo "### 6 · Por SSH: la llave no está en el servidor"
echo "gitserver\$ > /home/git/.ssh/authorized_keys   # alguien borra la llave de Jenkins"
G sh -c "cat /home/git/.ssh/authorized_keys > /tmp/ak && : > /home/git/.ssh/authorized_keys"
construir api-ssh
G sh -c "cat /tmp/ak > /home/git/.ssh/authorized_keys"
echo "(llave pública devuelta al servidor)"
construir api-ssh

echo
echo "### 7 · La llave mal pegada en la credencial"
echo "\$ jenkins update-credentials-by-xml system::system::jenkins _ git-ssh < cred-ssh-mal.xml   (la misma llave, con una línea en blanco delante)"
CLI update-credentials-by-xml system::system::jenkins _ git-ssh < ./_cred-ssh-mal.xml
construir api-ssh
echo
echo "jenkins\$ ssh-keygen -y -f llave   # la misma prueba en la terminal: llave buena, con línea en blanco, sin el salto final"
J sh -c 'cp /tmp/k /tmp/k-buena; { echo; cat /tmp/k; } > /tmp/k-blanco; head -c -1 /tmp/k > /tmp/k-sin-salto; chmod 600 /tmp/k-*; for f in /tmp/k-buena /tmp/k-blanco /tmp/k-sin-salto; do ssh-keygen -y -f $f 2>&1 | cut -c1-55; done'
echo "\$ jenkins update-credentials-by-xml system::system::jenkins _ git-ssh < cred-ssh.xml   (la llave tal cual)"
CLI update-credentials-by-xml system::system::jenkins _ git-ssh < ./_cred-ssh.xml
construir api-ssh
