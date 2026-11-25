# SALIDA — Jenkins: error fetching remote repo 'origin' (cultura-devops)

> Corrida del 2026-10-23 13:20. jenkins/jenkins:2.580.1-lts-jdk21 con el plugin de git; servidor git propio (alpine 3.22: git-http-backend + nginx, y sshd). Contraseñas y llaves de prueba.

```
### 0 · Versiones
jenkins$ jenkins --version ; git --version
2.580.1
git version 2.47.3
jenkins$ jenkins list-plugins | grep '^git '
git 5.11.0

### 1 · La URL: el repo cambió de nombre
$ jenkins build tienda   (consola, solo las líneas que importan)
Started tienda #1
 > git fetch --tags --force --progress -- http://gitserver/git/tienda.git +refs/heads/*:refs/remotes/origin/*
Checking out Revision <commit> (refs/remotes/origin/main)
Finished: SUCCESS

gitserver$ mv /srv/git/tienda.git /srv/git/tienda-web.git   # alguien renombra el repo
$ jenkins build tienda   (consola, solo las líneas que importan)
Started tienda #2
 > git fetch --tags --force --progress -- http://gitserver/git/tienda.git +refs/heads/*:refs/remotes/origin/*
ERROR: Error fetching remote repo 'origin'
Command "git fetch --tags --force --progress -- http://gitserver/git/tienda.git +refs/heads/*:refs/remotes/origin/*" returned status code 128:
stderr: fatal: repository 'http://gitserver/git/tienda.git/' not found
Finished: FAILURE

jenkins$ git ls-remote http://gitserver/git/tienda.git   # el mismo error, fuera de Jenkins
fatal: repository 'http://gitserver/git/tienda.git/' not found
jenkins$ git ls-remote http://gitserver/git/tienda-web.git
<commit>	HEAD
<commit>	refs/heads/main
(URL del trabajo corregida: http://gitserver/git/tienda-web.git)
$ jenkins build tienda   (consola, solo las líneas que importan)
Started tienda #3
 > git fetch --tags --force --progress -- http://gitserver/git/tienda-web.git +refs/heads/*:refs/remotes/origin/*
Checking out Revision <commit> (refs/remotes/origin/main)
Finished: SUCCESS

### 2 · Un trabajo NUEVO: el mismo error dice «cloning»
(URL con una letra de menos: tieda)
$ jenkins build tienda-nueva   (consola, solo las líneas que importan)
Started tienda-nueva #1
 > git fetch --tags --force --progress -- http://gitserver/git/tieda.git +refs/heads/*:refs/remotes/origin/*
ERROR: Error cloning remote repo 'origin'
Command "git fetch --tags --force --progress -- http://gitserver/git/tieda.git +refs/heads/*:refs/remotes/origin/*" returned status code 128:
stderr: fatal: repository 'http://gitserver/git/tieda.git/' not found
Finished: FAILURE

### 3 · Repo privado: sin credenciales
$ jenkins build api   (consola, solo las líneas que importan)
Started api #1
 > git fetch --tags --force --progress -- http://gitserver/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
ERROR: Error cloning remote repo 'origin'
Command "git fetch --tags --force --progress -- http://gitserver/git/privado/api.git +refs/heads/*:refs/remotes/origin/*" returned status code 128:
stderr: fatal: Authentication failed for 'http://gitserver/git/privado/api.git/'
Finished: FAILURE

jenkins$ git ls-remote http://gitserver/git/privado/api.git
fatal: could not read Username for 'http://gitserver': terminal prompts disabled
$ jenkins create-credentials-by-xml system::system::jenkins _ < cred-http.xml   (usuario jenkins, id git-http)
(el trabajo ahora usa credentialsId git-http)
$ jenkins build api   (consola, solo las líneas que importan)
Started api #2
 > git fetch --tags --force --progress -- http://gitserver/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
Checking out Revision <commit> (refs/remotes/origin/main)
Finished: SUCCESS

### 4 · Repo privado: el token caducó
gitserver$ htpasswd -b /etc/nginx/htpasswd jenkins token-nuevo   # el token viejo ya no vale
Updating password for user jenkins
$ jenkins build api   (consola, solo las líneas que importan)
Started api #3
 > git fetch --tags --force --progress -- http://gitserver/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
ERROR: Error fetching remote repo 'origin'
Command "git fetch --tags --force --progress -- http://gitserver/git/privado/api.git +refs/heads/*:refs/remotes/origin/*" returned status code 128:
stderr: fatal: Authentication failed for 'http://gitserver/git/privado/api.git/'
Finished: FAILURE

$ jenkins update-credentials-by-xml system::system::jenkins _ git-http < cred-http-nuevo.xml
$ jenkins build api   (consola, solo las líneas que importan)
Started api #4
 > git fetch --tags --force --progress -- http://gitserver/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
Checking out Revision <commit> (refs/remotes/origin/main)
Finished: SUCCESS

### 5 · Por SSH: la huella del servidor
(credencial git-ssh: la llave privada de Jenkins; su llave pública ya está en el servidor)
$ jenkins build api-ssh   (consola, solo las líneas que importan)
Started api-ssh #1
 > git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
ERROR: Error cloning remote repo 'origin'
Command "git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*" returned status code 128:
stderr: No ED25519 host key is known for gitserver and you have requested strict checking.
Host key verification failed.
fatal: Could not read from remote repository.
Finished: FAILURE

jenkins$ ssh-keyscan -t ed25519 gitserver >> ~/.ssh/known_hosts
# gitserver:22 SSH-2.0-OpenSSH_10.0
gitserver ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMKSlZX7F9ij3
$ jenkins build api-ssh   (consola, solo las líneas que importan)
Started api-ssh #2
 > git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
Checking out Revision <commit> (refs/remotes/origin/main)
Finished: SUCCESS

### 6 · Por SSH: la llave no está en el servidor
gitserver$ > /home/git/.ssh/authorized_keys   # alguien borra la llave de Jenkins
$ jenkins build api-ssh   (consola, solo las líneas que importan)
Started api-ssh #3
 > git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
ERROR: Error fetching remote repo 'origin'
Command "git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*" returned status code 128:
stderr: Permission denied, please try again.
Permission denied, please try again.
git@gitserver: Permission denied (publickey,password,keyboard-interactive).
fatal: Could not read from remote repository.
Finished: FAILURE
(llave pública devuelta al servidor)
$ jenkins build api-ssh   (consola, solo las líneas que importan)
Started api-ssh #4
 > git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
Checking out Revision <commit> (refs/remotes/origin/main)
Finished: SUCCESS

### 7 · La llave mal pegada en la credencial
$ jenkins update-credentials-by-xml system::system::jenkins _ git-ssh < cred-ssh-mal.xml   (la misma llave, con una línea en blanco delante)
$ jenkins build api-ssh   (consola, solo las líneas que importan)
Started api-ssh #5
 > git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
ERROR: Error fetching remote repo 'origin'
Command "git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*" returned status code 128:
stderr: Load key "/var/jenkins_home/workspace/api-ssh@tmp/jenkins-gitclient-ssh15700345626439075301.key": error in libcrypto
Permission denied, please try again.
Permission denied, please try again.
git@gitserver: Permission denied (publickey,password,keyboard-interactive).
fatal: Could not read from remote repository.
Finished: FAILURE

jenkins$ ssh-keygen -y -f llave   # la misma prueba en la terminal: llave buena, con línea en blanco, sin el salto final
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBmNQK6pFPoTOBVh9vO
Load key "/tmp/k-blanco": error in libcrypto
Load key "/tmp/k-sin-salto": error in libcrypto
$ jenkins update-credentials-by-xml system::system::jenkins _ git-ssh < cred-ssh.xml   (la llave tal cual)
$ jenkins build api-ssh   (consola, solo las líneas que importan)
Started api-ssh #6
 > git fetch --tags --force --progress -- git@gitserver:/srv/git/privado/api.git +refs/heads/*:refs/remotes/origin/*
Checking out Revision <commit> (refs/remotes/origin/main)
Finished: SUCCESS
```
