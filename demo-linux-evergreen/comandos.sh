#!/bin/bash
# Demo «Comandos Linux básicos» (cultura-devops, 2026-10-23). Corre DENTRO del contenedor como «ana», en ~/lab.
# Lo único que se borra es un fichero creado aquí mismo, por ruta relativa.
mkdir -p ~/lab && cd ~/lab || exit 1
p() { echo "\$ $*"; eval "$@" 2>&1; echo; }

echo "### Dónde estoy y quién soy"
p pwd
p whoami
p 'uname -sr'

echo "### Crear carpetas y ficheros"
p 'mkdir -p proyecto/logs'
p 'touch proyecto/notas.txt'
p 'printf "GET /\nGET /login\nPOST /login\nGET /\nGET /admin\nGET /\n" > proyecto/logs/acceso.log'
p 'echo "hola desde la terminal" > proyecto/notas.txt'
p 'ls'
p 'ls -l proyecto'
p 'cd proyecto && pwd && cd ..'

echo "### Leer"
p 'cat proyecto/notas.txt'
p 'head -n 2 proyecto/logs/acceso.log'
p 'tail -n 2 proyecto/logs/acceso.log'
p 'wc -l proyecto/logs/acceso.log'

echo "### Buscar"
p 'grep -n login proyecto/logs/acceso.log'
p 'grep -c "GET /$" proyecto/logs/acceso.log'
p 'find . -name "*.log"'
p 'sort proyecto/logs/acceso.log | uniq -c | sort -rn'

echo "### Copiar, mover, borrar"
p 'cp proyecto/notas.txt proyecto/notas.bak'
p 'mv proyecto/notas.bak proyecto/copia.txt'
p 'ls proyecto'
p 'rm proyecto/copia.txt'
p 'ls proyecto'

echo "### Permisos"
p 'printf "#!/bin/bash\necho funciona\n" > hola.sh'
p './hola.sh'
p 'chmod +x hola.sh'
p 'ls -l hola.sh | cut -d" " -f1,9'
p './hola.sh'

echo "### Comprimir"
p 'tar -czf proyecto.tar.gz proyecto'
p 'tar -tzf proyecto.tar.gz'

echo "### Procesos"
sleep 300 &
SPID=$!
p "ps -o pid,cmd -p $SPID"
p "kill $SPID"
sleep 0.3
p "ps -p $SPID || echo 'ya no existe'"

echo "### Disco y memoria"
p 'df -h / | sed "s/overlay */overlay /"'
p 'du -sh proyecto'
p 'free -h | head -2'

echo "### Ayuda"
p 'which tar'
p 'ls --help | head -n 3'
# Sin limpieza aquí: el contenedor entero se borra al terminar (ejecutar.sh).
