#!/usr/bin/env bash
# Leccion 2 — set -euo pipefail: lo que arregla, y lo que NO arregla.
cd "$(mktemp -d)" || exit 1

cat > sin_modo.sh <<'FIN'
#!/usr/bin/env bash
cp /no/existe/app.tar.gz ./app.tar.gz     # falla
echo "  desplegando $VERSION..."          # VERSION no existe: sale vacio
echo "  listo"
FIN

cat > con_modo.sh <<'FIN'
#!/usr/bin/env bash
set -euo pipefail
cp /no/existe/app.tar.gz ./app.tar.gz
echo "  desplegando $VERSION..."
echo "  listo"
FIN

echo "== 2.1 · Sin modo estricto: el script no se entera de nada =="
bash sin_modo.sh 2>&1 | sed 's/^/  /'
echo "  codigo de salida: ${PIPESTATUS[0]}   <- CERO. Todo bien, dice."

echo
echo "== 2.2 · Con set -euo pipefail =="
bash con_modo.sh 2>&1 | sed 's/^/  /'
echo "  codigo de salida: $(bash con_modo.sh >/dev/null 2>&1; echo $?)"
echo "  -e se para en el primer fallo · -u revienta con una variable sin definir"

echo
echo "== 2.3 · Que arregla pipefail =="
cat > tuberia.sh <<'FIN'
#!/usr/bin/env bash
set -eu
cat /no/existe | wc -l          # el cat falla, pero wc -l termina bien
echo "  la tuberia dijo que todo bien"
FIN
bash tuberia.sh 2>&1 | sed 's/^/  /'
echo "  El estado de una tuberia es el del ULTIMO comando. El error del cat se pierde."
cat > tuberia2.sh <<'FIN'
#!/usr/bin/env bash
set -euo pipefail
cat /no/existe | wc -l
echo "  esto ya no se imprime"
FIN
bash tuberia2.sh 2>&1 | sed 's/^/  /'
echo "  con pipefail, codigo $(bash tuberia2.sh >/dev/null 2>&1; echo $?)"

echo
echo "== 2.4 · LA TRAMPA: -e NO salta en todos lados =="
cat > enganos.sh <<'FIN'
#!/usr/bin/env bash
set -euo pipefail
comprobar() { grep -q "nada" /etc/hostname; }     # devuelve 1
if comprobar; then echo "casa"; else echo "  1) dentro de un if, el fallo NO para el script"; fi
comprobar || echo "  2) a la izquierda de || tampoco"
resultado=$(cat /no/existe 2>/dev/null) || true
echo "  3) y con || true te lo tragas a proposito: resultado=<$resultado>"
local_test() { local x=$(exit 3); echo "  4) local x=\$(...) devuelve $? (el de 'local', no el del comando)"; }
local_test
FIN
bash enganos.sh 2>&1 | sed 's/^/  /'
echo "  set -e ayuda, pero no es una red de seguridad: hay que mirar los codigos."

echo
echo "== 2.5 · La cabecera que se copia en todos los scripts =="
echo '  #!/usr/bin/env bash'
echo '  set -euo pipefail'
echo '  IFS=$'"'"'\n\t'"'"'      # separadores: salto de linea y tabulador, no el espacio'
