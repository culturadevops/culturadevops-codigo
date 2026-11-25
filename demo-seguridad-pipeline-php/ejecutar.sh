#!/bin/sh
# Corre dentro de composer:2 (PHP 8.5). Instala dependencias con versión fija y escanea las dos versiones de la app.
# Nota: se filtran los avisos «Deprecated:» que PHP 8.5 imprime al cargar guzzlehttp/promises 1.x (vendor/, no la app).
set -u
cd /demo
for d in app app-arreglada; do (cd $d && rm -f composer.lock && composer install -q --no-interaction --no-progress 2>&1 | grep -v '^Deprecated' | tail -2); done
q() { grep -v '^Deprecated:'; }
echo "### versiones"
php -v | head -1; composer --version 2>/dev/null | head -1
app/vendor/bin/psalm --version 2>&1 | q; app/vendor/bin/phpstan --version
echo
echo "### 1 · psalm normal (sin taint) sobre la app vulnerable"
echo "\$ vendor/bin/psalm"
(cd app && vendor/bin/psalm --no-progress --monochrome --output-format=compact 2>&1 | q | tail -n 8)
echo
echo "### 2 · psalm --taint-analysis sobre la app vulnerable"
echo "\$ vendor/bin/psalm --taint-analysis"
(cd app && vendor/bin/psalm --taint-analysis --no-progress --monochrome --output-format=compact 2>&1 | q)
echo
echo "### 2b · ¿por qué no salió la inyección SQL? La misma consulta con PDO y con mysqli"
echo "\$ vendor/bin/psalm --taint-analysis   # en pdo-vs-mysqli/"
(cd pdo-vs-mysqli && ../app/vendor/bin/psalm --taint-analysis --no-progress --monochrome --output-format=compact 2>&1 | q)
echo
echo "### 3 · phpstan nivel 9 sobre la app vulnerable"
echo "\$ vendor/bin/phpstan analyse"
(cd app && vendor/bin/phpstan analyse --no-progress --error-format=raw 2>&1)
echo
echo "### 4 · composer audit"
echo "\$ composer audit --no-dev --format=summary"
(cd app && composer audit --no-dev --format=summary 2>&1 | grep -v 'root package')
(cd app && composer audit --no-dev --format=json 2>/dev/null | php -r '$j=json_decode(stream_get_contents(STDIN),true); foreach($j["advisories"]["guzzlehttp/guzzle"] as $a){ echo $a["severity"]," · ",$a["cve"]," · ",$a["title"],PHP_EOL; }' | sort | uniq -c | sort -rn | head -20)
echo
echo "### 4b · ¿y si subo Guzzle a la 7.10.0? Composer ya no me deja"
mkdir -p /tmp/g710 && cd /tmp/g710
printf '{"require": {"guzzlehttp/guzzle": "7.10.0"}}
' > composer.json
echo "\$ composer update   # composer.json: guzzlehttp/guzzle 7.10.0"
composer update --no-install --no-interaction 2>&1 | q | grep -v '^$' | fold -w 150
echo
echo "### 4c · lo mismo con el bloqueo desactivado, para poder auditarla"
printf '{"require": {"guzzlehttp/guzzle": "7.10.0"}, "config": {"audit": {"block-insecure": false}}}
' > composer.json
composer update -q --no-install --no-interaction 2>&1 | q
echo "\$ composer audit --locked --no-dev --format=summary   # guzzle 7.10.0"
composer audit --locked --no-dev --format=summary 2>&1 | grep -v 'root package'
cd /demo
echo
echo "### 5 · el job del pipeline sobre la app vulnerable"
echo "\$ ./ci-seguridad.sh app"
sh ci-seguridad.sh app > /tmp/ci.txt 2>&1; c=$?; q < /tmp/ci.txt | grep -E '^(==|\| ERROR|Found|PIPELINE)'; echo "código de salida: $c"
echo
echo "### 6 · el mismo job sobre la app arreglada"
echo "\$ ./ci-seguridad.sh app-arreglada"
sh ci-seguridad.sh app-arreglada 2>&1 | q | grep -v 'root package'; echo "código de salida: $?"
echo
echo "### 7 · phpstan nivel 9 sobre la app arreglada"
(cd app-arreglada && vendor/bin/phpstan analyse --no-progress --error-format=raw 2>&1; echo "código de salida: $?")
