#!/bin/bash
# Demo «Variables de entorno en Linux» (cultura-devops, 2026-10-23). Corre DENTRO del contenedor como root.
# Usa al usuario «ana» para ver qué lee un shell de login y uno interactivo. Nada sale del contenedor.
p() { echo "\$ $*"; eval "$@" 2>&1; echo; }

echo "### 1 · Leer variables"
p 'echo $HOME'
p 'echo $PATH'
p 'printenv USER HOME SHELL 2>/dev/null || printenv HOME'
p 'env | sort | head -n 5'

echo "### 2 · Variable de shell vs variable de entorno"
p 'COLOR=azul; echo "en mi shell: $COLOR"'
p 'bash -c "echo \"en un programa hijo: [\$COLOR]\""'
p 'export COLOR; bash -c "echo \"en un programa hijo: [\$COLOR]\""'
unset COLOR

echo "### 3 · Solo para un comando"
p 'MODO=prueba bash -c "echo MODO=\$MODO"'
p 'echo "después: [$MODO]"'

echo "### 4 · Permanentes: .bashrc, .profile y /etc/environment"
su - ana -c 'echo "export EN_BASHRC=si" >> ~/.bashrc; echo "export EN_PROFILE=si" >> ~/.profile'
echo 'EN_ETC_ENVIRONMENT=si' >> /etc/environment
p "tail -n 1 /home/ana/.bashrc"
p "tail -n 1 /home/ana/.profile"
p "tail -n 1 /etc/environment"
echo "# Shell de login (como al entrar por SSH)"
p "su - ana -c 'echo bashrc=[\$EN_BASHRC] profile=[\$EN_PROFILE] etc=[\$EN_ETC_ENVIRONMENT]'"
echo "# Shell interactivo que no es de login (una terminal nueva dentro de la sesión)"
p "su ana -c 'bash -ic \"echo bashrc=[\\\$EN_BASHRC] profile=[\\\$EN_PROFILE] etc=[\\\$EN_ETC_ENVIRONMENT]\"' 2>/dev/null"
echo "# Un script o un servicio: ni login ni interactivo"
p "su ana -s /bin/bash -c 'env -i bash -c \"echo bashrc=[\\\$EN_BASHRC] profile=[\\\$EN_PROFILE] etc=[\\\$EN_ETC_ENVIRONMENT]\"'"

echo "### 5 · Por qué un secreto no va en una variable de entorno"
API_TOKEN=sk-demo-123456 sleep 300 &
PID=$!
sleep 0.3
p "tr '\0' '\n' < /proc/$PID/environ | grep TOKEN"
p "ps eww -p $PID | tr ' ' '\n' | grep TOKEN"
kill $PID 2>/dev/null
