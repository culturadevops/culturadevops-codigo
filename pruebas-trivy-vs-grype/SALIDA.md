# SALIDA — Trivy vs Grype (vídeo 338)

Generado 2026-10-07 23:49 UTC con `python correr.py`. Trivy (aquasec/trivy:latest) y Grype (anchore/grype:latest) sobre python:3.9-slim y alpine:3.22.

## 1 · La misma imagen: python:3.9-slim

### versiones

`$ trivy --version; grype version`

```
Version: 0.75.0
grype 0.120.1
```

## 2 · Escanear con cada uno

### tiempos (con las bases ya descargadas)

`$ time docker run … trivy / grype`

```
Trivy: 21 s
Grype: 78 s
```

### vulnerabilidades por severidad

`$ recuento de cada salida JSON`

```
severidad       Trivy    Grype
Critical            6       22
High              116      178
Medium            185      174
Low               156       36
Negligible          0       56
Unknown             2       36
TOTAL             465      502
```

## 3 · Por qué no coinciden

### solapamiento de CVE

`$ intersección de identificadores`

```
en los dos:   174
solo en Trivy: 15
solo en Grype: 53
```

### ejemplos que solo ve Trivy

`$ CVE y paquete`

```
TEMP-0841856-B18BAF  bash
CVE-2026-6357  pip
CVE-2025-8869  pip
CVE-2026-8643  pip
TEMP-0628843-DBAD28  login.defs
TEMP-0290435-0B57B5  tar
```

### ejemplos que solo ve Grype

`$ CVE y paquete`

```
CVE-2026-3276  python
CVE-2026-11972  python
CVE-2026-4360  python
GHSA-h35f-9h28-mq5c  setuptools
CVE-2025-15282  python
CVE-2026-4786  python
```

### fuentes de datos de Trivy

`$ campo DataSource de cada hallazgo`

```
Debian Security Tracker: 454
GitHub Security Advisory pip: 11
```

### fuentes de datos de Grype

`$ campo namespace de cada hallazgo`

```
debian:distro:debian:13: 448
nvd:cpe: 43
github:language:python: 11
```

## 4 · Solo las que tienen arreglo

### ¿cuántas se arreglan actualizando?

`$ FixedVersion / fix.versions`

```
Trivy: 300 de 465 con arreglo
Grype: 342 de 502 con arreglo
```

## 5 · Fallar la construcción si hay algo crítico

### Trivy en el pipeline

`$ trivy image --severity CRITICAL --exit-code 1`

```
│                         │                │          │        │                   │                  │ https://avd.aquasec.com/nvd/cve-2026-42496               │
│                         ├────────────────┤          │        │                   │                  ├──────────────────────────────────────────────────────────┤
│                         │ CVE-2026-8376  │          │        │                   │                  │ perl: Perl: Heap buffer overflow when compiling regular  │
│                         │                │          │        │                   │                  │ expressions on 32-bit builds...                          │
│                         │                │          │        │                   │                  │ https://avd.aquasec.com/nvd/cve-2026-8376                │
└─────────────────────────┴────────────────┴──────────┴────────┴───────────────────┴──────────────────┴──────────────────────────────────────────────────────────┘
código de salida: 1
```

### Grype en el pipeline

`$ grype --fail-on critical`

```
util-linux               2.41-5                       2.41.5-0+deb13u1                          deb     CVE-2026-53612       Unknown     N/A           N/A    
util-linux               2.41-5                       2.41.5-0+deb13u1                          deb     CVE-2026-53613       Unknown     N/A           N/A    
util-linux               2.41-5                       2.41.5-0+deb13u1                          deb     CVE-2026-53614       Unknown     N/A           N/A    
util-linux               2.41-5                       2.41.5-0+deb13u1                          deb     CVE-2026-53615       Unknown     N/A           N/A
```

## 6 · Una imagen limpia

### alpine:3.22

`$ escaneo con los dos`

```
severidad       Trivy    Grype
High                0        9
Medium              1       13
Low                 0        8
TOTAL               1       30
```
