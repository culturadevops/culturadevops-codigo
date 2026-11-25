# Salida real — seguridad en el pipeline para Java

Ejecutado el 2026-10-23T17:58Z.

```
### versiones
Apache Maven 3.9.16 (2bdd9fddda4b155ebf8000e807eb73fd829a51d5)
openjdk version "21.0.12.1" 2026-08-18 LTS
spotbugs-maven-plugin 4.9.3.0 · findsecbugs-plugin 1.14.0

### 1 · spotbugs con find security bugs sobre la app vulnerable
$ mvn compile spotbugs:check
Medium: This usage of java/lang/Runtime.exec([Ljava/lang/String;)Ljava/lang/Process; can be vulnerable to Command Injection [demo.Tienda] At Tienda.java:[line 31] COMMAND_INJECTION
Medium: Hardcoded constant database password in demo.Tienda.conectar() [demo.Tienda] At Tienda.java:[line 19] DMI_CONSTANT_DB_PASSWORD
High: Hard coded password found [demo.Tienda] At Tienda.java:[line 19] HARD_CODE_PASSWORD
Medium: This API (java/io/File.<init>(Ljava/lang/String;Ljava/lang/String;)V) reads a file whose location might be specified by user input [demo.Tienda] At Tienda.java:[line 36] PATH_TRAVERSAL_IN
Medium: This use of java/sql/Statement.executeQuery(Ljava/lang/String;)Ljava/sql/ResultSet; can be vulnerable to SQL injection (with JDBC) [demo.Tienda] At Tienda.java:[line 25] SQL_INJECTION_JDBC
High: demo.Tienda.producto(Connection, String) passes a nonconstant String to an execute or addBatch method on an SQL statement [demo.Tienda] At Tienda.java:[line 25] SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE
BugInstance size is 6
Total bugs: 6
código de salida de maven: 1

### 1b · el mismo análisis con <threshold>High</threshold> en el pom (copia en /tmp)
27:          <threshold>High</threshold>
$ mvn compile spotbugs:check
High: Hard coded password found [demo.Tienda] At Tienda.java:[line 19] HARD_CODE_PASSWORD
High: demo.Tienda.producto(Connection, String) passes a nonconstant String to an execute or addBatch method on an SQL statement [demo.Tienda] At Tienda.java:[line 25] SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE
BugInstance size is 2
Total bugs: 2
BUILD FAILURE
código de salida de maven: 1

### 2 · lo mismo sobre la app arreglada
$ mvn compile spotbugs:check
BugInstance size is 0
BUILD SUCCESS
código de salida de maven: 0

### 3 · trivy (dependencias del pom.xml) sobre la app vulnerable, solo HIGH y CRITICAL
$ trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 app/
Version: 0.75.0
2026-10-23T17:59:15Z	FATAL	Error	remote Maven repository returned 429 Too Many Requests for https://repo.maven.apache.org/maven2/org/apache/logging/log4j/log4j-core/2.14.1/log4j-core-2.14.1.pom. Retry-After: 1043.
The repository blocks all subsequent requests from this IP until the block clears.
To avoid this, populate the local Maven cache before scanning (e.g. run `mvn dependency:resolve`, or `mvn install` for a multi-module project, and cache ~/.m2 in CI).
código de salida de trivy: 1

### 4 · trivy sobre la app arreglada
$ trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 app-arreglada/
2026-10-23T17:59:15Z	FATAL	Error	remote Maven repository returned 429 Too Many Requests for https://repo.maven.apache.org/maven2/org/apache/logging/log4j/log4j-core/2.25.2/log4j-core-2.25.2.pom. Retry-After: 1042.
The repository blocks all subsequent requests from this IP until the block clears.
To avoid this, populate the local Maven cache before scanning (e.g. run `mvn dependency:resolve`, or `mvn install` for a multi-module project, and cache ~/.m2 in CI).
código de salida de trivy: 1

### 5 · trivy buscando secretos en el código (la clave de Stripe)
$ trivy fs --scanners secret --exit-code 1 app/src/

Report Summary

┌────────────────────────────┬──────┬─────────┐
│           Target           │ Type │ Secrets │
├────────────────────────────┼──────┼─────────┤
│ main/java/demo/Tienda.java │ text │    1    │
└────────────────────────────┴──────┴─────────┘
Legend:
- '-': Not scanned
- '0': Clean (no security findings detected)


main/java/demo/Tienda.java (secrets)
====================================
Total: 1 (UNKNOWN: 0, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 1)

CRITICAL: Stripe (stripe-secret-token)
════════════════════════════════════════
Stripe Secret Key
────────────────────────────────────────
 main/java/demo/Tienda.java:15 (offset: 464 bytes)
────────────────────────────────────────
  13   public class Tienda {
  14       // Fallo 4: una clave pegada en el código
  15 [     static final String STRIPE_API_KEY = "****************************************dG";
  16   
────────────────────────────────────────


código de salida de trivy: 1
```
