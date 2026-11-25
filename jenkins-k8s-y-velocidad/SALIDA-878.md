# SALIDA-878 · el pipeline de Spring PetClinic, mejora por mejora

> Corrida 2026-11-18 16:12 UTC. Generado por `velocidad/correr_878.py`. Candado `_logs/banco.lock` tomado.
> Otros contenedores vivos al empezar (carga ajena): jk-a-fijo, jk-a-jenkins. Docker: 24 CPU, 15.4 GiB.
> Jenkins 2.580.2 (jk-b-jenkins:2.580.2, plugins fijados), 4 ejecutores en el controlador; agentes `agent { docker }`.
> Proyecto: spring-petclinic en 500158f7 (2026-09-29; Spring Boot 4.1.0, Java 17) + 1 commit con los Jenkinsfile, rama `banco`, servido por file:// (sin red). Las dependencias SÍ bajan de Maven Central por internet (lo realista).
> Las dos pruebas que necesitan Docker (MySqlIntegrationTests, PostgresIntegrationTests) quedan fuera en TODAS las variantes (-Dtest con exclusión): el agente ve el socket de Docker del controlador y Testcontainers las arrancaba en la máquina.
> Imágenes ya descargadas en local antes de empezar (no se mide su descarga): sha256:6fdc855a6ed8 (maven) · sha256:41d5ea7e9ea0 (preparada).

## El checkout, aislado (git clone dentro del contenedor de Maven, 5 veces cada uno)
- completo: mediana 0.33 s (0.36, 0.33, 0.32, 0.31, 0.33) · .git 11.3 MiB · 1048 commits
- superficial --depth 1 --no-tags: mediana 0.10 s (0.10, 0.10, 0.10, 0.10, 0.10) · .git 0.6 MiB · 1 commits
- El mismo clone por internet, desde el repositorio público de spring-petclinic (rama main de hoy), 5 veces cada uno:
- completo (internet): mediana 2.48 s (2.87, 2.46, 2.44, 2.48, 3.52) · .git 11.3 MiB · 1047 commits
- superficial --depth 1 --no-tags (internet): mediana 1.53 s (1.70, 1.58, 1.48, 1.53, 1.51) · .git 0.7 MiB · 1 commits

- volumen `jk-b-m2` borrado antes de la ronda 1 → la caché de la ronda 1 es EN FRÍO

## Ronda 1 (calentamiento; no entra en la mediana)
- base #2: **121.0 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 93.0 · Pruebas 17.3 · Empaquetar 8.2
- paralelo #2: **107.2 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 3178 descargas de Maven Central (596 MB) · etapas: Pruebas y paquete 0.1 · Pruebas A 104.9 · Pruebas B 106.9 · Empaquetar 103.1
- cache #2: **115.9 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 87.9 · Pruebas 17.2 · Empaquetar 8.3
- imagen #2: **25.8 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 4.8 · Pruebas 14.0 · Empaquetar 4.5
- superficial #2: **123.2 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Checkout 0.2 · Compilar 94.8 · Pruebas 17.6 · Empaquetar 8.5
- todo #2: **18.3 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Pruebas y paquete 0.0 · Pruebas A 15.0 · Pruebas B 18.1 · Empaquetar 10.2

## Ronda 2
- base #3: **109.4 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 81.9 · Pruebas 16.8 · Empaquetar 8.2
- paralelo #3: **105.4 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 3171 descargas de Maven Central (578 MB) · etapas: Pruebas y paquete 0.0 · Pruebas A 100.6 · Pruebas B 105.2 · Empaquetar 99.2
- cache #3: **25.8 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Declarative: Checkout SCM 0.4 · Compilar 4.8 · Pruebas 14.0 · Empaquetar 4.5
- imagen #3: **25.6 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Declarative: Checkout SCM 0.4 · Compilar 4.8 · Pruebas 13.9 · Empaquetar 4.5
- superficial #3: **126.4 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Checkout 0.3 · Compilar 98.2 · Pruebas 17.6 · Empaquetar 8.2
- todo #3: **18.3 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Pruebas y paquete 0.1 · Pruebas A 15.2 · Pruebas B 18.1 · Empaquetar 10.5

## Ronda 3
- base #4: **122.8 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Declarative: Checkout SCM 0.4 · Compilar 94.6 · Pruebas 17.2 · Empaquetar 8.5
- paralelo #4: **115.1 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 3163 descargas de Maven Central (590 MB) · etapas: Pruebas y paquete 0.0 · Pruebas A 106.1 · Pruebas B 114.9 · Empaquetar 107.4
- cache #4: **25.6 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 4.8 · Pruebas 13.9 · Empaquetar 4.5
- imagen #4: **25.3 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 4.8 · Pruebas 13.7 · Empaquetar 4.5
- superficial #4: **118.1 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Checkout 0.2 · Compilar 90.8 · Pruebas 16.9 · Empaquetar 8.1
- todo #4: **18.7 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Pruebas y paquete 0.0 · Pruebas A 15.2 · Pruebas B 18.4 · Empaquetar 10.2

## Ronda 4
- base #5: **122.6 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Declarative: Checkout SCM 0.4 · Compilar 92.9 · Pruebas 19.0 · Empaquetar 8.2
- paralelo #5: **106.7 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 3165 descargas de Maven Central (577 MB) · etapas: Pruebas y paquete 0.1 · Pruebas A 100.5 · Pruebas B 106.5 · Empaquetar 102.4
- cache #5: **25.7 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 4.8 · Pruebas 14.0 · Empaquetar 4.5
- imagen #5: **25.5 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Declarative: Checkout SCM 0.3 · Compilar 4.8 · Pruebas 13.9 · Empaquetar 4.5
- superficial #5: **122.6 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 1087 descargas de Maven Central (210 MB) · etapas: Checkout 0.2 · Compilar 95.1 · Pruebas 17.1 · Empaquetar 8.0
- todo #5: **18.4 s** SUCCESS · pruebas 77 (fallos 0, saltadas 0) · .jar sí · 0 descargas de Maven Central (0 MB) · etapas: Pruebas y paquete 0.0 · Pruebas A 15.0 · Pruebas B 18.2 · Empaquetar 10.4

## ¿Mismo resultado en todas?
- base: (pruebas, saltadas, fallos, jar) = [(77, 0, 0, True)]
- paralelo: (pruebas, saltadas, fallos, jar) = [(77, 0, 0, True)]
- cache: (pruebas, saltadas, fallos, jar) = [(77, 0, 0, True)]
- imagen: (pruebas, saltadas, fallos, jar) = [(77, 0, 0, True)]
- superficial: (pruebas, saltadas, fallos, jar) = [(77, 0, 0, True)]
- todo: (pruebas, saltadas, fallos, jar) = [(77, 0, 0, True)]
- SÍ: las mismas pruebas pasadas y el .jar en todas las variantes

## Resumen (mediana de las rondas 2-4)
- base: **122.6 s** (109.4, 122.8, 122.6) · +0 % frente a la base · descargas 1087
- paralelo: **106.7 s** (105.4, 115.1, 106.7) · -13 % frente a la base · descargas 3165
- cache: **25.7 s** (25.8, 25.6, 25.7) · -79 % frente a la base · descargas 0
- imagen: **25.5 s** (25.6, 25.3, 25.5) · -79 % frente a la base · descargas 0
- superficial: **122.6 s** (126.4, 118.1, 122.6) · -0 % frente a la base · descargas 1087
- todo: **18.4 s** (18.3, 18.7, 18.4) · -85 % frente a la base · descargas 0
- caché EN FRÍO (ronda 1, volumen vacío): 115.9 s · 1087 descargas

## Etapas, mediana de las rondas 2-4 (s)
- base: Declarative: Checkout SCM 0.4 · Compilar 92.9 · Pruebas 17.2 · Empaquetar 8.2 · Declarative: Post Actions 0.0
- paralelo: Pruebas y paquete 0.0 · Pruebas A 100.6 · Pruebas B 106.5 · Empaquetar 102.4
- cache: Declarative: Checkout SCM 0.3 · Compilar 4.8 · Pruebas 14.0 · Empaquetar 4.5 · Declarative: Post Actions 0.0
- imagen: Declarative: Checkout SCM 0.3 · Compilar 4.8 · Pruebas 13.9 · Empaquetar 4.5 · Declarative: Post Actions 0.0
- superficial: Checkout 0.2 · Compilar 95.1 · Pruebas 17.1 · Empaquetar 8.1 · Declarative: Post Actions 0.0
- todo: Pruebas y paquete 0.0 · Pruebas A 15.2 · Pruebas B 18.2 · Empaquetar 10.4

## Tamaños (sin cronómetro, 2026-11-18T16:42:52Z)
`$ docker image ls` (DISK USAGE · CONTENT SIZE)
```
maven:3.9.11-eclipse-temurin-21  801MB
jk-b-agente-petclinic:1  1.21GB
```
`$ du -sh /root/.m2` en la imagen preparada y en el volumen jk-b-m2
```
215M	/root/.m2
215M	/root/.m2
```

## Anexo · la trampa del primer ensayo (build base del ensayo, sin excluir nada; consola guardada en velocidad/_prueba_base.txt)
```
2026-11-18T15:56:03.700Z  INFO 438 --- [           main] o.t.d.DockerClientProviderStrategy       : Found Docker environment with local Unix socket (unix:///var
2026-11-18T15:56:03.729Z  INFO 438 --- [           main] org.testcontainers.DockerClientFactory   : Connected to docker:
2026-11-18T15:56:04.003Z  INFO 438 --- [           main] tc.testcontainers/ryuk:0.14.0            : Creating container for image: testcontainers/ryuk:0.14.0
[INFO] Tests run: 0, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 31.16 s -- in org.springframework.samples.petclinic.PostgresIntegrationTests
[WARNING] Tests run: 2, Failures: 0, Errors: 0, Skipped: 2, Time elapsed: 0 s -- in org.springframework.samples.petclinic.MySqlIntegrationTests
[INFO] Tests run: 79, Failures: 0, Errors: 0, Skipped: 2
```
- Testcontainers encontró el socket de Docker del controlador, que el agente hereda por --volumes-from. PostgresIntegrationTests gastó 31 s para 0 pruebas y MySqlIntegrationTests salió saltada. Desde entonces las dos quedan excluidas en TODAS las variantes con -Dtest (77 pruebas en vez de 79). (Ese ensayo además falló al final por un paso junit sin el plugin junit instalado; se quitó.)
