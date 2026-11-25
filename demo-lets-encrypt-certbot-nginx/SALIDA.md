# SALIDA — Certificado SSL gratis con Let's Encrypt (certbot + nginx) (cultura-devops)

> Corrida del 2026-10-23 13:24. CA de prueba: Pebble version: v2.10.1 (b1e1ca4f3c30abb64111adaca4544bc5374cc306) (ghcr.io/letsencrypt/pebble:2.10.1, la CA de prueba oficial de Let's Encrypt).
> Servidor: Debian trixie, nginx version: nginx/1.26.3, certbot 4.0.0. Cliente: curlimages/curl:8.23.0. En producción se quita --server.

```
### 1 · Antes: el sitio solo tiene HTTP
web$ cat /etc/nginx/sites-available/tienda
server {
    listen 80;
    server_name tienda.example.com;
    root /var/www/tienda;
    index index.html;
}
$ curl -s http://tienda.example.com/
<h1>Mi tienda</h1>
$ curl https://tienda.example.com/
curl: (7) Failed to connect to tienda.example.com:443 after 0 ms: Could not connect to server

### 2 · certbot --nginx
web$ certbot --version
certbot 4.0.0
web$ certbot --nginx -d tienda.example.com -m admin@example.com --agree-tos --no-eff-email --redirect -n --server https://pebble:14000/dir
Saving debug log to /var/log/letsencrypt/letsencrypt.log
Account registered.
Requesting a certificate for tienda.example.com

Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/tienda.example.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/tienda.example.com/privkey.pem
This certificate expires on 2027-01-21.
These files will be updated when the certificate renews.
Certbot has set up a scheduled task to automatically renew this certificate in the background.

Deploying certificate
Successfully deployed certificate for tienda.example.com to /etc/nginx/sites-enabled/tienda
Congratulations! You have successfully enabled HTTPS on https://tienda.example.com

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
If you like Certbot, please consider supporting our work by:
 * Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
 * Donating to EFF:                    https://eff.org/donate-le
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

### 3 · Lo que certbot le cambió a la configuración de nginx
web$ diff /tmp/tienda.antes /etc/nginx/sites-available/tienda
2d1
<     listen 80;
5a5,11
> 
>     listen 443 ssl; # managed by Certbot
>     ssl_certificate /etc/letsencrypt/live/tienda.example.com/fullchain.pem; # managed by Certbot
>     ssl_certificate_key /etc/letsencrypt/live/tienda.example.com/privkey.pem; # managed by Certbot
>     include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
>     ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
> 
6a13,24
> server {
>     if ($host = tienda.example.com) {
>         return 301 https://$host$request_uri;
>     } # managed by Certbot
> 
> 
>     listen 80;
>     server_name tienda.example.com;
>     return 404; # managed by Certbot
> 
> 
> }
\ No newline at end of file
web$ nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

### 4 · Después: HTTP redirige y HTTPS funciona
$ curl -sI http://tienda.example.com/ | head -3
HTTP/1.1 301 Moved Permanently
Server: nginx
Date: Fri, 23 Oct 2026 18:24:27 GMT
$ curl -s https://tienda.example.com/   # el cliente confía en la raíz de Pebble
<h1>Mi tienda</h1>
$ curl https://tienda.example.com/   # un cliente que NO confía en Pebble
curl: (60) SSL certificate OpenSSL verify result: unable to get local issuer certificate (20)

### 5 · El certificado
web$ ls /etc/letsencrypt/live/tienda.example.com/
README
cert.pem
chain.pem
fullchain.pem
privkey.pem
web$ openssl x509 -in /etc/letsencrypt/live/tienda.example.com/cert.pem -noout -subject -issuer -dates -ext subjectAltName
subject=
issuer=CN=Pebble Intermediate CA 09dc2b
notBefore=Oct 23 18:24:24 2026 GMT
notAfter=Jan 21 18:24:23 2027 GMT
X509v3 Subject Alternative Name: critical
    DNS:tienda.example.com
web$ certbot certificates
Found the following certs:
  Certificate Name: tienda.example.com
    Serial Number: 76e38281f95a1cdc
    Key Type: ECDSA
    Domains: tienda.example.com
    Expiry Date: 2027-01-21 18:24:23+00:00 (VALID: 89 days)
    Certificate Path: /etc/letsencrypt/live/tienda.example.com/fullchain.pem
    Private Key Path: /etc/letsencrypt/live/tienda.example.com/privkey.pem

### 6 · La renovación: certbot renew --dry-run
web$ certbot renew --dry-run --no-random-sleep-on-renew   # el ensayo va SIEMPRE al staging de Let's Encrypt (y esta red no tiene internet)
Processing /etc/letsencrypt/renewal/tienda.example.com.conf
Failed to renew certificate tienda.example.com with error: HTTPSConnectionPool(host='acme-staging-v02.api.letsencrypt.org', port=443): Max retries exceeded with url: /directory (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1029)')))
All simulated renewals failed. The following certificates could not be renewed:
  /etc/letsencrypt/live/tienda.example.com/fullchain.pem (failure)
1 renew failure(s), 0 parse failure(s)
Ask for help or search for solutions at https://community.letsencrypt.org. See the logfile /var/log/letsencrypt/letsencrypt.log or re-run Certbot with -v for more details.
web$ certbot renew --dry-run --no-random-sleep-on-renew --server https://pebble:14000/dir   # el ensayo, contra la CA de prueba
Processing /etc/letsencrypt/renewal/tienda.example.com.conf
Simulating renewal of an existing certificate for tienda.example.com
Congratulations, all simulated renewals succeeded: 
  /etc/letsencrypt/live/tienda.example.com/fullchain.pem (success)
web$ certbot renew --no-random-sleep-on-renew   # sin forzar: todavía no toca
Processing /etc/letsencrypt/renewal/tienda.example.com.conf
Certificate not yet due for renewal
The following certificates are not due for renewal yet:
  /etc/letsencrypt/live/tienda.example.com/fullchain.pem expires on 2027-01-21 (skipped)
No renewals were attempted.
web$ certbot renew --force-renewal --no-random-sleep-on-renew   # una renovación de verdad
Processing /etc/letsencrypt/renewal/tienda.example.com.conf
Renewing an existing certificate for tienda.example.com
Reloading nginx server after certificate renewal
Congratulations, all renewals succeeded: 
  /etc/letsencrypt/live/tienda.example.com/fullchain.pem (success)
web$ openssl x509 -in /etc/letsencrypt/live/tienda.example.com/cert.pem -noout -dates
notBefore=Oct 23 18:24:38 2026 GMT
notAfter=Jan 21 18:24:37 2027 GMT

### 7 · Quién renueva solo: el temporizador que instala el paquete
web$ cat /lib/systemd/system/certbot.timer
[Unit]
Description=Run certbot twice daily

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=43200
Persistent=true

[Install]
WantedBy=timers.target
web$ grep -v '^#' /etc/cron.d/certbot | grep .
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
0 */12 * * * root test -x /usr/bin/certbot -a \! -d /run/systemd/system && perl -e 'sleep int(rand(43200))' && certbot -q renew --no-random-sleep-on-renew
web$ cat /etc/letsencrypt/renewal/tienda.example.com.conf | grep -E 'authenticator|installer|server'
server = https://pebble:14000/dir
authenticator = nginx
installer = nginx

### 8 · Cuando el desafío falla: un dominio que no apunta a este servidor
web$ certbot --nginx -d www.tienda.example.com -m admin@example.com --agree-tos --no-eff-email -n --server https://pebble:14000/dir
Requesting a certificate for www.tienda.example.com
Certbot failed to authenticate some domains (authenticator: nginx). The Certificate Authority reported these problems:
  Domain: www.tienda.example.com
  Type:   connection
  Detail: Get "http://www.tienda.example.com:80/.well-known/acme-challenge/DJwz7t_oJFpOsUaQAPCnY5-5As89BaMOWj1PCiI7e7k": error occurred while resolving URL "http://www.tienda.example.com:80/.well-known/acme-challenge/DJwz7t_oJFpOsUaQAPCnY5-5As89BaMOWj1PCiI7e7k": lookup www.tienda.example.com on 127.0.0.11:53: no such host
Hint: The Certificate Authority failed to verify the temporary nginx configuration changes made by Certbot. Ensure the listed domains point to this nginx server and that it is accessible from the internet.
Some challenges have failed.
Ask for help or search for solutions at https://community.letsencrypt.org. See the logfile /var/log/letsencrypt/letsencrypt.log or re-run Certbot with -v for more details.
```
