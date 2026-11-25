# -*- coding: utf-8 -*-
"""Genera los archivos de la demo «seguridad en el pipeline para Java» (cultura-devops). python generar.py"""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))


def W(p, t):
    p = os.path.join(AQUI, p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)


POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>demo</groupId>
  <artifactId>tienda</artifactId>
  <version>1.0</version>
  <properties>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.apache.logging.log4j</groupId>
      <artifactId>log4j-core</artifactId>
      <version>LOG4J</version>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>com.github.spotbugs</groupId>
        <artifactId>spotbugs-maven-plugin</artifactId>
        <version>4.9.3.0</version>
        <configuration>
          <effort>Max</effort>
          <threshold>Low</threshold>
          <failOnError>true</failOnError>
          <includeFilterFile>spotbugs-seguridad.xml</includeFilterFile>
          <plugins>
            <plugin>
              <groupId>com.h3xstream.findsecbugs</groupId>
              <artifactId>findsecbugs-plugin</artifactId>
              <version>1.14.0</version>
            </plugin>
          </plugins>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""

FILTRO = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Solo la categoría de seguridad (la de Find Security Bugs) -->
<FindBugsFilter>
  <Match><Bug category="SECURITY"/></Match>
</FindBugsFilter>
"""

VULN = """package demo;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/** Tienda de ejemplo con 4 fallos de seguridad PUESTOS A PROPÓSITO (demo de cultura-devops). No la despliegues. */
public class Tienda {
    // Fallo 4: una clave pegada en el código
    static final String STRIPE_API_KEY = "CLAVE_STRIPE_FALSA_DE_EJEMPLO";

    Connection conectar() throws SQLException {
        // Fallo 4b: usuario y contraseña de la base pegados en el código
        return DriverManager.getConnection("jdbc:postgresql://db/tienda", "admin", "admin123");
    }

    // Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
    String producto(Connection db, String nombre) throws SQLException {
        Statement st = db.createStatement();
        ResultSet rs = st.executeQuery("SELECT nombre, precio FROM productos WHERE nombre = '" + nombre + "'");
        return rs.next() ? rs.getString(1) : "";
    }

    // Fallo 2: inyección de comandos
    Process ping(String host) throws IOException {
        return Runtime.getRuntime().exec(new String[] {"sh", "-c", "ping -c 1 " + host});
    }

    // Fallo 3: path traversal (archivo=../../etc/passwd sale de la carpeta)
    String factura(String archivo) throws IOException {
        return Files.readString(new File("/srv/facturas", archivo).toPath());
    }
}
"""

ARREGLADA = """package demo;

import java.io.IOException;
import java.net.InetAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/** La misma tienda, con los fallos arreglados (demo de cultura-devops). */
public class Tienda {
    private static final Path FACTURAS = Path.of("/srv/facturas").toAbsolutePath().normalize();

    // Arreglo 4: las claves vienen del entorno (en el pipeline, de un gestor de secretos)
    static String stripeKey() {
        return System.getenv("STRIPE_API_KEY");
    }

    Connection conectar() throws SQLException {
        return DriverManager.getConnection(System.getenv("DB_URL"), System.getenv("DB_USER"), System.getenv("DB_PASS"));
    }

    // Arreglo 1: consulta preparada con parámetros
    String producto(Connection db, String nombre) throws SQLException {
        try (PreparedStatement st = db.prepareStatement("SELECT nombre, precio FROM productos WHERE nombre = ?")) {
            st.setString(1, nombre);
            try (ResultSet rs = st.executeQuery()) {
                return rs.next() ? rs.getString(1) : "";
            }
        }
    }

    // Arreglo 2: solo IPs literales, y sin shell
    boolean ping(String host) throws IOException {
        if (!host.matches("[0-9.]{7,15}")) {
            throw new IllegalArgumentException("IP no válida");
        }
        return InetAddress.getByName(host).isReachable(2000);
    }

    // Arreglo 3: la ruta final tiene que quedar dentro de FACTURAS
    String factura(String archivo) throws IOException {
        Path ruta = FACTURAS.resolve(archivo).normalize();
        if (!ruta.startsWith(FACTURAS)) {
            throw new IllegalArgumentException("ruta fuera de facturas");
        }
        return Files.readString(ruta);
    }
}
"""

SB = "com.github.spotbugs:spotbugs-maven-plugin:4.9.3.0"

EJECUTAR = """#!/bin/sh
# Corre dentro de maven:3.9-eclipse-temurin-21. El escaneo de dependencias va aparte, con trivy (ver correr.sh).
set -u
cd /demo
hallazgos() { grep -E '^.(ERROR|INFO). (Medium|High|Low|Scary|Scariest|Troubling|Of Concern):' | sed 's/^.[A-Z]*. //' | cut -c1-240; }
echo "### versiones"
mvn -v 2>/dev/null | head -1; java -version 2>&1 | head -1
echo "spotbugs-maven-plugin 4.9.3.0 · findsecbugs-plugin 1.14.0"
echo
echo "### 1 · spotbugs con find security bugs sobre la app vulnerable"
echo "\\$ mvn compile spotbugs:check"
cd app; mvn -B compile SB:check > /tmp/a.txt 2>&1; c=$?; cd ..
hallazgos < /tmp/a.txt
grep -E 'Total bugs|BugInstance size' /tmp/a.txt | sed 's/^.[A-Z]*. //'
echo "código de salida de maven: $c"
echo
echo "### 1b · el mismo análisis con <threshold>High</threshold> en el pom (copia en /tmp)"
rm -rf /tmp/app-high && cp -r app /tmp/app-high && sed -i 's|<threshold>Low</threshold>|<threshold>High</threshold>|' /tmp/app-high/pom.xml
grep -n '<threshold>' /tmp/app-high/pom.xml
echo "\$ mvn compile spotbugs:check"
cd /tmp/app-high; mvn -B compile SB:check > /tmp/h.txt 2>&1; c=$?; cd /demo
hallazgos < /tmp/h.txt
grep -E 'Total bugs|BugInstance size|BUILD' /tmp/h.txt | sed 's/^.[A-Z]*. //'
echo "código de salida de maven: $c"
echo
echo "### 2 · lo mismo sobre la app arreglada"
echo "\\$ mvn compile spotbugs:check"
cd app-arreglada; mvn -B compile SB:check > /tmp/b.txt 2>&1; c=$?; cd ..
hallazgos < /tmp/b.txt
grep -E 'Total bugs|BugInstance size|BUILD' /tmp/b.txt | sed 's/^.[A-Z]*. //'
echo "código de salida de maven: $c"
""".replace("SB:check", SB + ":check")

CORRER = """#!/bin/sh
# Lanza la demo en Docker y guarda la salida en SALIDA.md. El repositorio de maven y la base de trivy quedan en volúmenes aparte.
cd "$(dirname "$0")"
D="$(pwd -W 2>/dev/null || pwd)"
T="docker run --rm -v $D:/demo -v demo-trivy-cache:/root/.cache aquasec/trivy:0.75.0"
{ echo '# Salida real — seguridad en el pipeline para Java'; echo; echo "Ejecutado el $(date -u +%Y-%m-%dT%H:%MZ)."; echo; echo '```'
  MSYS_NO_PATHCONV=1 docker run --rm -v "$D:/demo" -v demo-java-m2:/root/.m2 maven:3.9-eclipse-temurin-21 sh /demo/ejecutar.sh
  echo
  echo "### 3 · trivy (dependencias del pom.xml) sobre la app vulnerable, solo HIGH y CRITICAL"
  echo "\\$ trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 app/"
  MSYS_NO_PATHCONV=1 $T --version | head -1
  MSYS_NO_PATHCONV=1 $T fs --quiet --scanners vuln --severity HIGH,CRITICAL --exit-code 1 /demo/app; echo "código de salida de trivy: $?"
  echo
  echo "### 4 · trivy sobre la app arreglada"
  echo "\\$ trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 app-arreglada/"
  MSYS_NO_PATHCONV=1 $T fs --quiet --scanners vuln --severity HIGH,CRITICAL --exit-code 1 /demo/app-arreglada; echo "código de salida de trivy: $?"
  echo
  echo "### 5 · trivy buscando secretos en el código (la clave de Stripe)"
  echo "\\$ trivy fs --scanners secret --exit-code 1 app/src/"
  MSYS_NO_PATHCONV=1 $T fs --quiet --scanners secret --exit-code 1 /demo/app/src; echo "código de salida de trivy: $?"
  echo '```'; } > SALIDA.md 2>&1
"""

W("app/pom.xml", POM.replace("LOG4J", "2.14.1"))
W("app/spotbugs-seguridad.xml", FILTRO)
W("app/src/main/java/demo/Tienda.java", VULN)
W("app-arreglada/pom.xml", POM.replace("LOG4J", "2.25.2"))
W("app-arreglada/spotbugs-seguridad.xml", FILTRO)
W("app-arreglada/src/main/java/demo/Tienda.java", ARREGLADA)
W("ejecutar.sh", EJECUTAR)
W("correr.sh", CORRER)
print("ok")
