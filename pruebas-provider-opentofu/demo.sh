#!/usr/bin/env bash
# demo.sh — la medición del vídeo 236 «Escribe un proveedor de OpenTofu y entiende el apply».
#
# Todo dentro de `banco-tofu` (golang:1.26-bookworm + OpenTofu 1.12.6 como binario suelto).
#
# ⛔ EL PRIMER INTENTO SE ENSEÑA TAL CUAL FALLA. El encargo lo pide y además es lo honesto:
#    instalar un proveedor local tiene fricción de rutas y de versiones, y cortar el vídeo justo
#    antes del error es lo que hace que la gente crea que a ella le pasa algo raro.
#
# ⚠️ Nada se da por bueno sin verlo: el fichero se mira con `cat`, el estado se abre, y el desvío
#    se provoca a mano tocando el fichero por fuera.
set -u
export MSYS_NO_PATHCONV=1

echo "== 1 · EL PROVEEDOR ES UN BINARIO APARTE =="
( cd /lab/provider && go build -o /lab/terraform-provider-ficherito . ) || { echo "no compila"; exit 1; }
echo "   tamaño: $(stat -c %s /lab/terraform-provider-ficherito) bytes"
echo -n "   y si lo ejecuto suelto: "
/lab/terraform-provider-ficherito 2>&1 | head -1

echo
echo "== 2 · ⛔ PRIMER INTENTO: tofu init SIN instalarlo. El fallo, tal cual =="
cd /lab/demo
rm -rf .terraform .terraform.lock.hcl terraform.tfstate* salida 2>/dev/null
tofu init 2>&1 | grep -vE "^$" | head -12
echo "   >>> salió con ${PIPESTATUS[0]}"

echo
echo "== 3 · LA INSTALACIÓN QUE SÍ FUNCIONA: el espejo de sistema de ficheros =="
DEST=/root/.terraform.d/plugins/registry.opentofu.org/lab/ficherito/0.1.0/linux_amd64
mkdir -p "$DEST"
cp /lab/terraform-provider-ficherito "$DEST/terraform-provider-ficherito_v0.1.0"
chmod +x "$DEST/terraform-provider-ficherito_v0.1.0"
echo "   puesto en:"
echo "     ~/.terraform.d/plugins/registry.opentofu.org/lab/ficherito/0.1.0/linux_amd64/"
echo "   ⚠️ la ruta lleva dentro el espacio de nombres, la versión Y la arquitectura."
echo "      Si te equivocas en una sola parte, el error dice «no encontrado», no «mal puesto»."
echo
tofu init 2>&1 | grep -E "Installing|installed|successfully|Error" | head -6

echo
echo "== 4 · PLAN: qué va a hacer, y por qué =="
tofu plan -no-color 2>&1 | grep -vE "^$|Refreshing|^─" | head -20

echo
echo "== 5 · APPLY, y LOS DOS PROCESOS a la vez =="
( for i in $(seq 1 40); do
    ps -eo comm= 2>/dev/null | grep -E "^(tofu|terraform-prov)" | sort -u > /tmp/procs.txt
    if [ "$(wc -l < /tmp/procs.txt)" -ge 2 ]; then cp /tmp/procs.txt /tmp/procs-pillados.txt; fi
    sleep 0.15
  done ) &
ESPIA=$!
tofu apply -auto-approve -no-color 2>&1 | grep -E "Creating|Creation complete|Apply complete" | head -5
wait $ESPIA 2>/dev/null
echo "   procesos vivos durante el apply:"
sed 's/^/     /' /tmp/procs-pillados.txt 2>/dev/null || echo "     (no se pillaron los dos a la vez)"

echo
echo "== 5b · 🥇 LA PRUEBA DE QUE SON DOS PROCESOS: la traza del protocolo =="
echo "   (el apply tarda 0 s, así que no da tiempo a pillarlos con 'ps'."
echo "    La traza sí lo demuestra: arranque del complemento, su PID y su gRPC)"
rm -rf /lab/salida terraform.tfstate* 2>/dev/null
TF_LOG=trace tofu apply -auto-approve -no-color >/tmp/traza.log 2>&1
grep -oE "plugin process exited|starting plugin|plugin address|pid=[0-9]+|network=\"unix\"|address=\"/tmp/plugin[0-9]+\"|using plugin: version=[0-9]+" /tmp/traza.log \
  | sort -u | head -8 | sed 's/^/     /'
echo "   llamadas del protocolo que hizo OpenTofu al proveedor:"
grep -oE "tf_rpc=[A-Za-z]+" /tmp/traza.log | sort -u | sed 's/tf_rpc=/     /' | head -12

echo
echo "== 6 · ¿EXISTE EL FICHERO DE VERDAD? =="
echo -n "   contenido en disco: "; cat /lab/salida/hola.txt 2>&1; echo

echo
echo "== 7 · EL ESTADO: lo que OpenTofu cree que hay =="
tofu show -json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for r in d.get('values',{}).get('root_module',{}).get('resources',[]):
    print('     direccion:', r['address'])
    print('     tipo:     ', r['type'])
    for k,v in sorted(r['values'].items()):
        print(f'       {k:<10} = {v!r}')
" 2>/dev/null || sed -n '1,25p' terraform.tfstate

echo
echo "== 8 · 🥇 EL DESVÍO: toco el fichero POR FUERA y vuelvo a planificar =="
echo "   escribo otra cosa en el fichero, sin pasar por OpenTofu:"
echo "me lo cambio a mano" > /lab/salida/hola.txt
echo -n "     ahora dice: "; cat /lab/salida/hola.txt
echo
echo "   y ahora tofu plan:"
tofu plan -no-color 2>&1 | grep -vE "^$|^─" | grep -E "changed outside|~|will be updated|No changes|Plan:" | head -12

echo
echo "== 9 · ⛔ ¿Y SI BORRO EL FICHERO? (el Read que devuelve «ya no está») =="
rm -f /lab/salida/hola.txt
tofu plan -no-color 2>&1 | grep -E "will be created|has been deleted|Plan:|No changes" | head -6

echo
echo "== 10 · DESTROY: y comprobar que de verdad no queda nada =="
tofu apply -auto-approve -no-color >/dev/null 2>&1   # lo recrea para poder destruirlo
tofu destroy -auto-approve -no-color 2>&1 | grep -E "Destroying|Destruction complete|Destroy complete" | head -4
echo -n "   ¿queda el fichero? "; [ -f /lab/salida/hola.txt ] && echo "SÍ (mal)" || echo "no"
echo -n "   recursos en el estado: "; tofu state list 2>/dev/null | wc -l

echo
echo "== fin =="
