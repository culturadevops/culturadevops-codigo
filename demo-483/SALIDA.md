$ cat limpiar.sh   # típico de lo que genera una IA
#!/bin/bash
# Borra los temporales de la app
DIR=$APP_TMP
cd $DIR
rm -rf $DIR/*
echo "limpieza terminada"

$ shellcheck limpiar.sh
In limpiar.sh line 4:
^-----^ SC2164 (warning): Use 'cd ... || exit' or 'cd ... || return' in case cd fails.
   ^--^ SC2086 (info): Double quote to prevent globbing and word splitting.
In limpiar.sh line 5:
       ^----^ SC2115 (warning): Use "${var:?}" to ensure this never expands to /* .
       ^--^ SC2086 (info): Double quote to prevent globbing and word splitting.
  https://www.shellcheck.net/wiki/SC2115 -- Use "${var:?}" to ensure this nev...
  https://www.shellcheck.net/wiki/SC2164 -- Use 'cd ... || exit' or 'cd ... |...
  https://www.shellcheck.net/wiki/SC2086 -- Double quote to prevent globbing ...

$ # ¿y si APP_TMP llega vacía? (con echo delante: se imprime, NO se ejecuta)
rm -rf /bin /boot /dev /etc /home /lib /lib64 /media /mnt /opt /proc /root /run /sbin /srv /sys /tmp /usr /var
limpieza terminada

$ shellcheck limpiar-revisado.sh
(código de salida: 0)

$ APP_TMP="" bash limpiar-revisado.sh
limpiar-revisado.sh: line 4: APP_TMP: APP_TMP no está definida
(código de salida: 1)

$ # ahora con una carpeta temporal de verdad
$ ls $APP_TMP
a.tmp
b.tmp
$ bash limpiar-revisado.sh
limpieza terminada en /tmp/tmp.cJPQT0wSHc
$ ls $APP_TMP
(vacía)
$ ls / | head -3   # el sistema sigue intacto
bin
boot
dev

$ shellcheck --version
version: 0.11.0
