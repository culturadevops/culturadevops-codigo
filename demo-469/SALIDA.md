$ openssl s_client -connect letsencrypt.org:443 -servername letsencrypt.org </dev/null 2>/dev/null | openssl x509 -noout -issuer -startdate -enddate
issuer=C=US, O=Let's Encrypt, CN=YE2
notBefore=Sep  4 14:34:32 2026 GMT
notAfter=Dec  3 14:34:31 2026 GMT

$ openssl req -x509 -newkey rsa:2048 -nodes -days 10 -subj "/CN=demo.local" -keyout k.pem -out c.pem
  (certificado de prueba creado)
$ openssl x509 -in c.pem -noout -checkend $((30*86400)); echo $?
Certificate will expire
  código de salida: 1
$ openssl x509 -in c.pem -noout -checkend $((5*86400)); echo $?
Certificate will not expire
  código de salida: 0

$ cat vigilar.sh
#!/usr/bin/env bash
# Avisa si algún certificado caduca en menos de UMBRAL días.
UMBRAL=${UMBRAL:-30}
for sitio in "$@"; do
  fin=$(openssl s_client -connect "$sitio:443" -servername "$sitio" </dev/null 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  [ -z "$fin" ] && { echo "ERROR  $sitio: no pude leer el certificado"; continue; }
  d=$(( ( $(date -d "$fin" +%s) - $(date +%s) ) / 86400 ))
  [ "$d" -lt "$UMBRAL" ] && echo "AVISO  $sitio caduca en $d días" || echo "ok     $sitio: $d días"
done

$ bash vigilar.sh letsencrypt.org go.dev github.com sitio-que-no-existe.invalid
ok     letsencrypt.org: 48 días
ok     go.dev: 64 días
ok     github.com: 44 días
ERROR  sitio-que-no-existe.invalid: no pude leer el certificado
$ UMBRAL=200 bash vigilar.sh letsencrypt.org go.dev github.com
AVISO  letsencrypt.org caduca en 48 días
AVISO  go.dev caduca en 64 días
AVISO  github.com caduca en 44 días
