# SALIDA · demo-git-errores (2026-10-23, git 2.47.3, OpenSSH_10.0p2, Debian trixie en Docker)

Ejecutado con `bash correr.sh` desde Git Bash. «github» es un servidor SSH local (usuario git con git-shell y repos --bare) que hace de GitHub; nada sale a Internet ni usa tokens. Hallazgo B6b: tras un --force ajeno, `git pull --rebase` (modo fork-point, git-merge-base docs) descarta el commit que el remoto «descartó»: hay que recuperarlo del reflog.

```
=================== A · Permission denied (publickey) ===================
### A1 · Sin llave: el error
ana$ git clone git@github:proyecto.git 2>&1; echo exit=$?
Cloning into 'proyecto'...
Warning: Permanently added 'github' (ED25519) to the list of known hosts.
git@github: Permission denied (publickey).
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
exit=128
ana$ ls ~/.ssh 2>&1
known_hosts

### A2 · ssh -T: probar SOLO la autenticación
ana$ ssh -T -o StrictHostKeyChecking=accept-new -o BatchMode=yes git@github; echo exit=$?
git@github: Permission denied (publickey).
exit=255

### A3 · Crear la llave
ana$ ssh-keygen -t ed25519 -C ana@ejemplo.com -f ~/.ssh/id_ed25519 -N '' | head -3
Generating public/private ed25519 key pair.
Your identification has been saved in /home/ana/.ssh/id_ed25519
Your public key has been saved in /home/ana/.ssh/id_ed25519.pub
ana$ ls ~/.ssh
id_ed25519
id_ed25519.pub
known_hosts
ana$ cat ~/.ssh/id_ed25519.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF7p2bT8yOZkOPAk8gewErpk5IfdfZZzQs5PrhLeTneC ana@ejemplo.com

### A4 · Aún sin registrar la pública en el servidor: sigue fallando, y ssh -vT dice por qué
ana$ ssh -vT -o StrictHostKeyChecking=accept-new -o BatchMode=yes git@github 2>&1 | grep -E 'Offering|Authentications that can continue|Permission denied' | head -6
debug1: Authentications that can continue: publickey
debug1: Offering public key: /home/ana/.ssh/id_ed25519 ED25519 SHA256:WHwKVOCXtfiIGe+Tagdo0XTpAuxOe087sQFraEd5u9I
debug1: Authentications that can continue: publickey
git@github: Permission denied (publickey).

### A5 · Registrar la pública (en GitHub: Settings → SSH and GPG keys → New SSH key)
(pegada en authorized_keys del servidor)
ana$ ssh -T -o StrictHostKeyChecking=accept-new -o BatchMode=yes git@github; echo exit=$?
Linux github 6.18.33.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun 18 21:54:43 UTC 2026 x86_64
Hi! You've successfully authenticated, but this server does not provide shell access.
exit=128

### A6 · Ahora sí
ana$ git clone git@github:proyecto.git 2>&1; echo exit=$?
Cloning into 'proyecto'...
warning: You appear to have cloned an empty repository.
exit=0

### A7 · El remoto en https vs ssh, y cómo cambiarlo
ana$ cd proyecto && git remote -v
origin	git@github:proyecto.git (fetch)
origin	git@github:proyecto.git (push)
ana$ cd proyecto && git remote set-url origin https://github.com/ana/proyecto.git && git remote -v
origin	https://github.com/ana/proyecto.git (fetch)
origin	https://github.com/ana/proyecto.git (push)
ana$ cd proyecto && git remote set-url origin git@github:proyecto.git && git remote -v
origin	git@github:proyecto.git (fetch)
origin	git@github:proyecto.git (push)

### A7b · Con https, ¿qué credencial guarda git?
ana$ cd proyecto && git config --get credential.helper || echo '(ninguno configurado)'
(ninguno configurado)

### A8 · Una llave que no es la tuya: beto con su propia llave no registrada
beto$ ssh-keygen -q -t ed25519 -f ~/.ssh/id_ed25519 -N '' && ssh -T -o StrictHostKeyChecking=accept-new -o BatchMode=yes git@github; echo exit=$?
Warning: Permanently added 'github' (ED25519) to the list of known hosts.
git@github: Permission denied (publickey).
exit=255

=================== C · Los 15 comandos básicos ===================
### C1 · git config
ana$ git config --global user.name && git config --global user.email
Ana
ana@ejemplo.com
### C2 · git init + C3 · git status
ana$ mkdir mi-app && cd mi-app && git init && git status
Initialized empty Git repository in /home/ana/mi-app/.git/
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to track)
### C4 · git add + C5 · git commit
ana$ cd mi-app && echo 'print("hola")' > app.py && echo '# Mi app' > README.md && git status --short && git add . && git status --short && git commit -m 'Primer commit'
?? README.md
?? app.py
A  README.md
A  app.py
[main (root-commit) 54befe1] Primer commit
 2 files changed, 2 insertions(+)
 create mode 100644 README.md
 create mode 100644 app.py
### C6 · git log
ana$ cd mi-app && echo 'print("adiós")' >> app.py && git commit -qam 'Despedida' && git log --oneline
ede7467 Despedida
54befe1 Primer commit
### C7 · git diff
ana$ cd mi-app && echo 'print("versión 2")' >> app.py && git diff
diff --git a/app.py b/app.py
index 0eab88c..df1f06e 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 print("hola")
 print("adiós")
+print("versión 2")
### C8 · git restore
ana$ cd mi-app && git restore app.py && git status --short && echo '(limpio)'
(limpio)
### C9 · git branch + C10 · git switch
ana$ cd mi-app && git branch login && git branch && git switch login
  login
* main
Switched to branch 'login'
ana$ cd mi-app && echo 'def login(): pass' > login.py && git add login.py && git commit -qm 'Login' && git log --oneline
a534532 Login
ede7467 Despedida
54befe1 Primer commit
### C11 · git merge
ana$ cd mi-app && git switch -q main && git merge login && git log --oneline --graph
Updating ede7467..a534532
Fast-forward
 login.py | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 login.py
* a534532 Login
* ede7467 Despedida
* 54befe1 Primer commit
### C12 · git remote + C13 · git push
ana$ cd mi-app && git remote add origin git@github:mi-app.git && git remote -v && git push -u origin main 2>&1
origin	git@github:mi-app.git (fetch)
origin	git@github:mi-app.git (push)
To github:mi-app.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
### C14 · git clone
beto$ git clone git@github:mi-app.git 2>&1 && ls mi-app
Cloning into 'mi-app'...
README.md
app.py
login.py
### C15 · git pull
beto$ cd mi-app && echo 'Instrucciones' >> README.md && git commit -qam 'README' && git push -q 2>&1 && git log --oneline -1
b836c77 README
ana$ cd mi-app && git pull 2>&1 && git log --oneline -3
From github:mi-app
   a534532..b836c77  main       -> origin/main
Updating a534532..b836c77
Fast-forward
 README.md | 1 +
 1 file changed, 1 insertion(+)
b836c77 README
a534532 Login
ede7467 Despedida

=================== B · push rejected (non-fast-forward) ===================
ana$ git clone -q git@github:equipo.git 2>&1; cd equipo && echo 'v1' > app.txt && git add . && git commit -qm 'v1' && git push -q origin main 2>&1 && git log --oneline
warning: You appear to have cloned an empty repository.
f924735 v1
beto$ git clone -q git@github:equipo.git 2>&1 && cd equipo && git log --oneline
f924735 v1
### B1 · Los dos trabajan a la vez; ana empuja primero
ana$ cd equipo && echo 'login de ana' > login.txt && git add . && git commit -qm 'Login (ana)' && git push origin main 2>&1
To github:equipo.git
   f924735..16bacd9  main -> main
beto$ cd equipo && echo 'pagos de beto' > pagos.txt && git add . && git commit -qm 'Pagos (beto)' && git push origin main 2>&1; echo exit=$?
To github:equipo.git
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'github:equipo.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.
exit=1

### B2 · Qué pasó: el remoto tiene un commit que beto no tiene
beto$ cd equipo && git fetch -q && git status -sb | head -1 && git log --oneline --graph --all
## main...origin/main [ahead 1, behind 1]
* 5e40245 Pagos (beto)
| * 16bacd9 Login (ana)
|/  
* f924735 v1

### B2b · El mismo push, ahora que beto ya hizo fetch: el motivo cambia a non-fast-forward
beto$ cd equipo && git push origin main 2>&1; echo exit=$?
To github:equipo.git
 ! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to 'github:equipo.git'
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart. If you want to integrate the remote changes,
hint: use 'git pull' before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.
exit=1

### B3 · git pull sin decir cómo (git moderno pregunta)
beto$ cd equipo && git pull 2>&1 | head -12; echo exit=$?
hint: You have divergent branches and need to specify how to reconcile them.
hint: You can do so by running one of the following commands sometime before
hint: your next pull:
hint:
hint:   git config pull.rebase false  # merge
hint:   git config pull.rebase true   # rebase
hint:   git config pull.ff only       # fast-forward only
hint:
hint: You can replace "git config" with "git config --global" to set a default
hint: preference for all repositories. You can also pass --rebase, --no-rebase,
hint: or --ff-only on the command line to override the configured default per
hint: invocation.
exit=0

### B4 · Opción 1: git pull --rebase (historia en línea)
beto$ cd equipo && git pull --rebase 2>&1 && git log --oneline --graph && git push origin main 2>&1
Rebasing (1/1)Successfully rebased and updated refs/heads/main.
* fa01698 Pagos (beto)
* 16bacd9 Login (ana)
* f924735 v1
To github:equipo.git
   16bacd9..fa01698  main -> main

### B5 · Opción 2: git pull --no-rebase (merge: queda un commit de unión)
ana$ cd equipo && git pull -q --rebase 2>&1; echo '(ana al día)'
(ana al día)
beto$ cd equipo && git pull -q --rebase 2>&1; echo '(beto al día)'
(beto al día)
ana$ cd equipo && echo 'ajuste de ana' >> login.txt && git commit -qam 'Ajuste login (ana)' && git push -q origin main 2>&1 && echo '(ana empujó otra vez)'
(ana empujó otra vez)
beto$ cd equipo && echo 'ajuste de beto' >> pagos.txt && git commit -qam 'Ajuste pagos (beto)' && git push origin main 2>&1 | tail -3
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.
beto$ cd equipo && git pull --no-rebase --no-edit 2>&1 | tail -3 && git log --oneline --graph | head -8 && git push origin main 2>&1
Merge made by the 'ort' strategy.
 login.txt | 1 +
 1 file changed, 1 insertion(+)
*   bdc5c48 Merge branch 'main' of github:equipo
|\  
| * e0218a7 Ajuste login (ana)
* | d1827a4 Ajuste pagos (beto)
|/  
* fa01698 Pagos (beto)
* 16bacd9 Login (ana)
* f924735 v1
To github:equipo.git
   e0218a7..bdc5c48  main -> main

### B6 · La tentación: --force (y lo que se lleva)
ana$ cd equipo && git pull -q --no-rebase --no-edit 2>&1; echo 'reporte' > reporte.txt && git add . && git commit -qm 'Reporte (ana)' && git push -q origin main 2>&1 && git log --oneline -3
47696d3 Reporte (ana)
bdc5c48 Merge branch 'main' of github:equipo
d1827a4 Ajuste pagos (beto)
beto$ cd equipo && echo 'otra cosa' > otra.txt && git add . && git commit -qm 'Otra cosa (beto)' && git push --force origin main 2>&1
To github:equipo.git
 + 47696d3...179884d main -> main (forced update)
ana$ cd equipo && git fetch -q && echo '--- el remoto ahora:' && git log --oneline -4 origin/main && echo '--- ¿está el commit de ana?' && (git branch -r --contains $(git rev-parse HEAD) | grep -q origin/main && echo sí || echo 'NO: --force lo borró del remoto')
--- el remoto ahora:
179884d Otra cosa (beto)
bdc5c48 Merge branch 'main' of github:equipo
d1827a4 Ajuste pagos (beto)
e0218a7 Ajuste login (ana)
--- ¿está el commit de ana?
NO: --force lo borró del remoto

### B6b · Recuperar el commit de ana (sigue en su copia local)
ana$ cd equipo && git log --oneline -1 && git pull --rebase 2>&1 | tail -1 && git push origin main 2>&1 | tail -1 && git log --oneline -3
47696d3 Reporte (ana)
Successfully rebased and updated refs/heads/main.
Everything up-to-date
179884d Otra cosa (beto)
bdc5c48 Merge branch 'main' of github:equipo
d1827a4 Ajuste pagos (beto)

### B6c · Dónde quedó: el reflog, y recuperarlo con cherry-pick
ana$ cd equipo && git reflog -4
179884d HEAD@{0}: pull --rebase (finish): returning to refs/heads/main
179884d HEAD@{1}: pull --rebase (start): checkout 179884dc8413caeeaa9babba570bd712b86aabb0
47696d3 HEAD@{2}: commit: Reporte (ana)
bdc5c48 HEAD@{3}: pull -q --no-rebase --no-edit: Fast-forward
ana$ cd equipo && git cherry-pick 'HEAD@{2}' 2>&1 | head -1 && git push origin main 2>&1 | tail -1 && git log --oneline -3
[main 3c632d0] Reporte (ana)
   179884d..3c632d0  main -> main
3c632d0 Reporte (ana)
179884d Otra cosa (beto)
bdc5c48 Merge branch 'main' of github:equipo

### B7 · --force-with-lease: se niega si el remoto cambió desde tu último fetch
ana$ cd equipo && git reset -q --hard origin/main && echo 'urgente' > urgente.txt && git add . && git commit -qm 'Urgente (ana)' && git push -q origin main 2>&1 && echo '(ana empujó)'
(ana empujó)
beto$ cd equipo && echo 'otra más' > otra2.txt && git add . && git commit -qm 'Otra más (beto)' && git push --force-with-lease origin main 2>&1; echo exit=$?
To github:equipo.git
 ! [rejected]        main -> main (stale info)
error: failed to push some refs to 'github:equipo.git'
exit=1

### B8 · Elegir una vez y olvidarse: pull.rebase
beto$ cd equipo && git reset -q --hard HEAD~1 && git config pull.rebase true && echo 'nota' > nota.txt && git add . && git commit -qm 'Nota (beto)' && git pull 2>&1 | tail -1 && git push origin main 2>&1 | tail -1 && git log --oneline -3
Rebasing (1/1)Successfully rebased and updated refs/heads/main.
   2d0f6e5..9a93144  main -> main
9a93144 Nota (beto)
2d0f6e5 Urgente (ana)
3c632d0 Reporte (ana)

=================== versiones ===================
ana$ git --version && ssh -V 2>&1
git version 2.47.3
OpenSSH_10.0p2 Debian-7+deb13u4, OpenSSL 3.5.7 9 Jun 2026
(contenedores y red de la demo borrados)
```
