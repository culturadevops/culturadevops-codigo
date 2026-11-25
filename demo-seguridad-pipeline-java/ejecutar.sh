#!/bin/sh
# Corre dentro de maven:3.9-eclipse-temurin-21. El escaneo de dependencias va aparte, con trivy (ver correr.sh).
set -u
cd /demo
hallazgos() { grep -E '^.(ERROR|INFO). (Medium|High|Low|Scary|Scariest|Troubling|Of Concern):' | sed 's/^.[A-Z]*. //' | cut -c1-240; }
echo "### versiones"
mvn -v 2>/dev/null | head -1; java -version 2>&1 | head -1
echo "spotbugs-maven-plugin 4.9.3.0 · findsecbugs-plugin 1.14.0"
echo
echo "### 1 · spotbugs con find security bugs sobre la app vulnerable"
echo "\$ mvn compile spotbugs:check"
cd app; mvn -B compile com.github.spotbugs:spotbugs-maven-plugin:4.9.3.0:check > /tmp/a.txt 2>&1; c=$?; cd ..
hallazgos < /tmp/a.txt
grep -E 'Total bugs|BugInstance size' /tmp/a.txt | sed 's/^.[A-Z]*. //'
echo "código de salida de maven: $c"
echo
echo "### 1b · el mismo análisis con <threshold>High</threshold> en el pom (copia en /tmp)"
rm -rf /tmp/app-high && cp -r app /tmp/app-high && sed -i 's|<threshold>Low</threshold>|<threshold>High</threshold>|' /tmp/app-high/pom.xml
grep -n '<threshold>' /tmp/app-high/pom.xml
echo "\$ mvn compile spotbugs:check"
cd /tmp/app-high; mvn -B compile com.github.spotbugs:spotbugs-maven-plugin:4.9.3.0:check > /tmp/h.txt 2>&1; c=$?; cd /demo
hallazgos < /tmp/h.txt
grep -E 'Total bugs|BugInstance size|BUILD' /tmp/h.txt | sed 's/^.[A-Z]*. //'
echo "código de salida de maven: $c"
echo
echo "### 2 · lo mismo sobre la app arreglada"
echo "\$ mvn compile spotbugs:check"
cd app-arreglada; mvn -B compile com.github.spotbugs:spotbugs-maven-plugin:4.9.3.0:check > /tmp/b.txt 2>&1; c=$?; cd ..
hallazgos < /tmp/b.txt
grep -E 'Total bugs|BugInstance size|BUILD' /tmp/b.txt | sed 's/^.[A-Z]*. //'
echo "código de salida de maven: $c"
