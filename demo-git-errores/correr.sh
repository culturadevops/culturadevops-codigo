#!/bin/bash
# Demos de git (cultura-devops, 2026-10-23) para tres vídeos:
#   A · «Permission denied (publickey)» y cómo diagnosticarlo con ssh -T / ssh -vT
#   B · «git push rejected (non-fast-forward)»: pull --rebase, merge, --force y --force-with-lease
#   C · «Comandos git básicos»: los 15 de todos los días
# Un contenedor «github» (sshd + usuario git con git-shell + repos --bare) hace de GitHub; «pc» es tu máquina.
# ⛔ Nada sale a Internet ni a GitHub de verdad; no hay tokens. Corre desde Git Bash.
set -u
cd "$(dirname "$0")"
IMG=cd-demo-git:1
docker build -q -t $IMG . >/dev/null
docker rm -f github pc >/dev/null 2>&1; docker network rm red-git >/dev/null 2>&1
docker network create red-git >/dev/null
docker run -d --name github --hostname github --network red-git --label demo=cd-git $IMG sleep infinity >/dev/null
docker run -d --name pc --hostname pc --network red-git --label demo=cd-git $IMG sleep infinity >/dev/null
G() { docker exec github bash -c "$*" 2>&1; }
# «ana» y «beto» son dos personas en dos máquinas; para no levantar tres contenedores, son dos usuarios de «pc».
docker exec pc bash -c "useradd -m -s /bin/bash ana; useradd -m -s /bin/bash beto"
A() { echo "ana\$ $*"; docker exec -u ana -w /home/ana pc bash -c "$*" 2>&1; }
Bt() { echo "beto\$ $*"; docker exec -u beto -w /home/beto pc bash -c "$*" 2>&1; }
for u in ana beto; do
  docker exec -u $u pc bash -c "git config --global user.name ${u^}; git config --global user.email $u@ejemplo.com; git config --global init.defaultBranch main; git config --global core.sshCommand 'ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes'"
done

# El «GitHub» local: usuario git con git-shell (como GitHub: no da shell), un repo vacío, y sshd sin contraseñas.
G "useradd -m -s /usr/bin/git-shell git && mkdir -p /home/git/.ssh /home/git/git-shell-commands && chmod 700 /home/git/.ssh"
G "cat > /home/git/git-shell-commands/no-interactive-login <<'EOF'
#!/bin/sh
printf '%s\n' \"Hi! You've successfully authenticated, but this server does not provide shell access.\"
exit 128
EOF
chmod +x /home/git/git-shell-commands/no-interactive-login"
G "git init -q --bare -b main /home/git/proyecto.git && chown -R git:git /home/git"
G "rm -f /etc/motd && sed -i 's/^#\?PrintMotd.*/PrintMotd no/; s/^#\?PrintLastLog.*/PrintLastLog no/' /etc/ssh/sshd_config && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && ssh-keygen -A >/dev/null && /usr/sbin/sshd"
SSHOPT="-o StrictHostKeyChecking=accept-new -o BatchMode=yes"

echo "=================== A · Permission denied (publickey) ==================="
echo "### A1 · Sin llave: el error"
A "git clone git@github:proyecto.git 2>&1; echo exit=\$?"
A "ls ~/.ssh 2>&1"
echo
echo "### A2 · ssh -T: probar SOLO la autenticación"
A "ssh -T $SSHOPT git@github; echo exit=\$?"
echo
echo "### A3 · Crear la llave"
A "ssh-keygen -t ed25519 -C ana@ejemplo.com -f ~/.ssh/id_ed25519 -N '' | head -3"
A "ls ~/.ssh"
A "cat ~/.ssh/id_ed25519.pub"
echo
echo "### A4 · Aún sin registrar la pública en el servidor: sigue fallando, y ssh -vT dice por qué"
A "ssh -vT $SSHOPT git@github 2>&1 | grep -E 'Offering|Authentications that can continue|Permission denied' | head -6"
echo
echo "### A5 · Registrar la pública (en GitHub: Settings → SSH and GPG keys → New SSH key)"
docker exec -u ana pc cat /home/ana/.ssh/id_ed25519.pub | docker exec -i github bash -c "cat >> /home/git/.ssh/authorized_keys; chown git:git /home/git/.ssh/authorized_keys; chmod 600 /home/git/.ssh/authorized_keys"
echo "(pegada en authorized_keys del servidor)"
A "ssh -T $SSHOPT git@github; echo exit=\$?"
echo
echo "### A6 · Ahora sí"
A "git clone git@github:proyecto.git 2>&1; echo exit=\$?"
echo
echo "### A7 · El remoto en https vs ssh, y cómo cambiarlo"
A "cd proyecto && git remote -v"
A "cd proyecto && git remote set-url origin https://github.com/ana/proyecto.git && git remote -v"
A "cd proyecto && git remote set-url origin git@github:proyecto.git && git remote -v"
echo
echo "### A7b · Con https, ¿qué credencial guarda git?"
A "cd proyecto && git config --get credential.helper || echo '(ninguno configurado)'"
echo
echo "### A8 · Una llave que no es la tuya: beto con su propia llave no registrada"
Bt "ssh-keygen -q -t ed25519 -f ~/.ssh/id_ed25519 -N '' && ssh -T $SSHOPT git@github; echo exit=\$?"

# beto también registrado, para el bloque B
docker exec -u beto pc cat /home/beto/.ssh/id_ed25519.pub | docker exec -i github bash -c "cat >> /home/git/.ssh/authorized_keys"

echo
echo "=================== C · Los 15 comandos básicos ==================="
echo "### C1 · git config"
A "git config --global user.name && git config --global user.email"
echo "### C2 · git init + C3 · git status"
A "mkdir mi-app && cd mi-app && git init && git status"
echo "### C4 · git add + C5 · git commit"
A "cd mi-app && echo 'print(\"hola\")' > app.py && echo '# Mi app' > README.md && git status --short && git add . && git status --short && git commit -m 'Primer commit'"
echo "### C6 · git log"
A "cd mi-app && echo 'print(\"adiós\")' >> app.py && git commit -qam 'Despedida' && git log --oneline"
echo "### C7 · git diff"
A "cd mi-app && echo 'print(\"versión 2\")' >> app.py && git diff"
echo "### C8 · git restore"
A "cd mi-app && git restore app.py && git status --short && echo '(limpio)'"
echo "### C9 · git branch + C10 · git switch"
A "cd mi-app && git branch login && git branch && git switch login"
A "cd mi-app && echo 'def login(): pass' > login.py && git add login.py && git commit -qm 'Login' && git log --oneline"
echo "### C11 · git merge"
A "cd mi-app && git switch -q main && git merge login && git log --oneline --graph"
echo "### C12 · git remote + C13 · git push"
G "git init -q --bare -b main /home/git/mi-app.git && chown -R git:git /home/git/mi-app.git"
A "cd mi-app && git remote add origin git@github:mi-app.git && git remote -v && git push -u origin main 2>&1"
echo "### C14 · git clone"
Bt "git clone git@github:mi-app.git 2>&1 && ls mi-app"
echo "### C15 · git pull"
Bt "cd mi-app && echo 'Instrucciones' >> README.md && git commit -qam 'README' && git push -q 2>&1 && git log --oneline -1"
A "cd mi-app && git pull 2>&1 && git log --oneline -3"

echo
echo "=================== B · push rejected (non-fast-forward) ==================="
G "git init -q --bare -b main /home/git/equipo.git && chown -R git:git /home/git/equipo.git"
A "git clone -q git@github:equipo.git 2>&1; cd equipo && echo 'v1' > app.txt && git add . && git commit -qm 'v1' && git push -q origin main 2>&1 && git log --oneline"
Bt "git clone -q git@github:equipo.git 2>&1 && cd equipo && git log --oneline"
echo "### B1 · Los dos trabajan a la vez; ana empuja primero"
A "cd equipo && echo 'login de ana' > login.txt && git add . && git commit -qm 'Login (ana)' && git push origin main 2>&1"
Bt "cd equipo && echo 'pagos de beto' > pagos.txt && git add . && git commit -qm 'Pagos (beto)' && git push origin main 2>&1; echo exit=\$?"
echo
echo "### B2 · Qué pasó: el remoto tiene un commit que beto no tiene"
Bt "cd equipo && git fetch -q && git status -sb | head -1 && git log --oneline --graph --all"
echo
echo "### B2b · El mismo push, ahora que beto ya hizo fetch: el motivo cambia a non-fast-forward"
Bt "cd equipo && git push origin main 2>&1; echo exit=\$?"
echo
echo "### B3 · git pull sin decir cómo (git moderno pregunta)"
Bt "cd equipo && git pull 2>&1 | head -12; echo exit=\$?"
echo
echo "### B4 · Opción 1: git pull --rebase (historia en línea)"
Bt "cd equipo && git pull --rebase 2>&1 && git log --oneline --graph && git push origin main 2>&1"
echo
echo "### B5 · Opción 2: git pull --no-rebase (merge: queda un commit de unión)"
A "cd equipo && git pull -q --rebase 2>&1; echo '(ana al día)'"
Bt "cd equipo && git pull -q --rebase 2>&1; echo '(beto al día)'"
A "cd equipo && echo 'ajuste de ana' >> login.txt && git commit -qam 'Ajuste login (ana)' && git push -q origin main 2>&1 && echo '(ana empujó otra vez)'"
Bt "cd equipo && echo 'ajuste de beto' >> pagos.txt && git commit -qam 'Ajuste pagos (beto)' && git push origin main 2>&1 | tail -3"
Bt "cd equipo && git pull --no-rebase --no-edit 2>&1 | tail -3 && git log --oneline --graph | head -8 && git push origin main 2>&1"
echo
echo "### B6 · La tentación: --force (y lo que se lleva)"
A "cd equipo && git pull -q --no-rebase --no-edit 2>&1; echo 'reporte' > reporte.txt && git add . && git commit -qm 'Reporte (ana)' && git push -q origin main 2>&1 && git log --oneline -3"
Bt "cd equipo && echo 'otra cosa' > otra.txt && git add . && git commit -qm 'Otra cosa (beto)' && git push --force origin main 2>&1"
A "cd equipo && git fetch -q && echo '--- el remoto ahora:' && git log --oneline -4 origin/main && echo '--- ¿está el commit de ana?' && (git branch -r --contains \$(git rev-parse HEAD) | grep -q origin/main && echo sí || echo 'NO: --force lo borró del remoto')"
echo
echo "### B6b · Recuperar el commit de ana (sigue en su copia local)"
A "cd equipo && git log --oneline -1 && git pull --rebase 2>&1 | tail -1 && git push origin main 2>&1 | tail -1 && git log --oneline -3"

echo
echo "### B6c · Dónde quedó: el reflog, y recuperarlo con cherry-pick"
A "cd equipo && git reflog -4"
A "cd equipo && git cherry-pick 'HEAD@{2}' 2>&1 | head -1 && git push origin main 2>&1 | tail -1 && git log --oneline -3"

echo
echo "### B7 · --force-with-lease: se niega si el remoto cambió desde tu último fetch"
A "cd equipo && git reset -q --hard origin/main && echo 'urgente' > urgente.txt && git add . && git commit -qm 'Urgente (ana)' && git push -q origin main 2>&1 && echo '(ana empujó)'"
Bt "cd equipo && echo 'otra más' > otra2.txt && git add . && git commit -qm 'Otra más (beto)' && git push --force-with-lease origin main 2>&1; echo exit=\$?"

echo
echo "### B8 · Elegir una vez y olvidarse: pull.rebase"
Bt "cd equipo && git reset -q --hard HEAD~1 && git config pull.rebase true && echo 'nota' > nota.txt && git add . && git commit -qm 'Nota (beto)' && git pull 2>&1 | tail -1 && git push origin main 2>&1 | tail -1 && git log --oneline -3"

echo
echo "=================== versiones ==================="
A "git --version && ssh -V 2>&1"
docker rm -f github pc >/dev/null && docker network rm red-git >/dev/null && echo "(contenedores y red de la demo borrados)"
