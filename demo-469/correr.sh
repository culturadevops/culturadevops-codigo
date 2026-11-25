#!/usr/bin/env bash
# Demo del vídeo 469 «Certificados TLS que caducan» — se EJECUTA y su salida va a SALIDA.md.
#   1) cuándo caduca el certificado de un sitio real (openssl s_client);
#   2) un certificado de prueba que caduca en 10 días, y la comprobación «¿caduca en menos de 30 días?» (-checkend);
#   3) un vigilante de 10 líneas que revisa una lista de sitios y avisa con días restantes.
# Certificados de prueba en un directorio temporal.
set -u
T=$(mktemp -d)
cd "$T"
dias() {   # días hasta que caduca el certificado PEM que llega por stdin
  fin=$(openssl x509 -noout -enddate | cut -d= -f2)
  echo $(( ( $(date -d "$fin" +%s) - $(date +%s) ) / 86400 ))
}
echo '$ openssl s_client -connect letsencrypt.org:443 -servername letsencrypt.org </dev/null 2>/dev/null | openssl x509 -noout -issuer -startdate -enddate'
openssl s_client -connect letsencrypt.org:443 -servername letsencrypt.org </dev/null 2>/dev/null | openssl x509 -noout -issuer -startdate -enddate
echo

echo '$ openssl req -x509 -newkey rsa:2048 -nodes -days 10 -subj "/CN=demo.local" -keyout k.pem -out c.pem'
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 10 -subj "/CN=demo.local" -keyout k.pem -out c.pem 2>/dev/null && echo "  (certificado de prueba creado)"
echo '$ openssl x509 -in c.pem -noout -checkend $((30*86400)); echo $?'
openssl x509 -in c.pem -noout -checkend $((30*86400)); echo "  código de salida: $?"
echo '$ openssl x509 -in c.pem -noout -checkend $((5*86400)); echo $?'
openssl x509 -in c.pem -noout -checkend $((5*86400)); echo "  código de salida: $?"
echo

cat > vigilar.sh <<'EOF'
#!/usr/bin/env bash
# Avisa si algún certificado caduca en menos de UMBRAL días.
UMBRAL=${UMBRAL:-30}
for sitio in "$@"; do
  fin=$(openssl s_client -connect "$sitio:443" -servername "$sitio" </dev/null 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  [ -z "$fin" ] && { echo "ERROR  $sitio: no pude leer el certificado"; continue; }
  d=$(( ( $(date -d "$fin" +%s) - $(date +%s) ) / 86400 ))
  [ "$d" -lt "$UMBRAL" ] && echo "AVISO  $sitio caduca en $d días" || echo "ok     $sitio: $d días"
done
EOF
echo '$ cat vigilar.sh'
cat vigilar.sh
echo
echo '$ bash vigilar.sh letsencrypt.org go.dev github.com sitio-que-no-existe.invalid'
bash vigilar.sh letsencrypt.org go.dev github.com sitio-que-no-existe.invalid
echo '$ UMBRAL=200 bash vigilar.sh letsencrypt.org go.dev github.com'
UMBRAL=200 bash vigilar.sh letsencrypt.org go.dev github.com
cd / && rm -rf "$T"
