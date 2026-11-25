# SALIDA — entorno (cultura-devops, tanda evergreen de Linux)

> Corrida del 2026-10-23 12:51 en un contenedor: Ubuntu 24.04.4 LTS, GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu).

```
### 1 · Leer variables
$ echo $HOME
/root

$ echo $PATH
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

$ printenv USER HOME SHELL 2>/dev/null || printenv HOME
/root
/root

$ env | sort | head -n 5
HOME=/root
HOSTNAME=servidor
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PWD=/root
SHLVL=1

### 2 · Variable de shell vs variable de entorno
$ COLOR=azul; echo "en mi shell: $COLOR"
en mi shell: azul

$ bash -c "echo \"en un programa hijo: [\$COLOR]\""
en un programa hijo: []

$ export COLOR; bash -c "echo \"en un programa hijo: [\$COLOR]\""
en un programa hijo: [azul]

### 3 · Solo para un comando
$ MODO=prueba bash -c "echo MODO=\$MODO"
MODO=prueba

$ echo "después: [$MODO]"
después: []

### 4 · Permanentes: .bashrc, .profile y /etc/environment
$ tail -n 1 /home/ana/.bashrc
export EN_BASHRC=si

$ tail -n 1 /home/ana/.profile
export EN_PROFILE=si

$ tail -n 1 /etc/environment
EN_ETC_ENVIRONMENT=si

# Shell de login (como al entrar por SSH)
$ su - ana -c 'echo bashrc=[$EN_BASHRC] profile=[$EN_PROFILE] etc=[$EN_ETC_ENVIRONMENT]'
bashrc=[] profile=[si] etc=[si]

# Shell interactivo que no es de login (una terminal nueva dentro de la sesión)
$ su ana -c 'bash -ic "echo bashrc=[\$EN_BASHRC] profile=[\$EN_PROFILE] etc=[\$EN_ETC_ENVIRONMENT]"' 2>/dev/null
bashrc=[si] profile=[] etc=[si]

# Un script o un servicio: ni login ni interactivo
$ su ana -s /bin/bash -c 'env -i bash -c "echo bashrc=[\$EN_BASHRC] profile=[\$EN_PROFILE] etc=[\$EN_ETC_ENVIRONMENT]"'
bashrc=[] profile=[] etc=[]

### 5 · Por qué un secreto no va en una variable de entorno
$ tr '\0' '\n' < /proc/36/environ | grep TOKEN
API_TOKEN=sk-demo-123456

$ ps eww -p 36 | tr ' ' '\n' | grep TOKEN
API_TOKEN=sk-demo-123456

```
