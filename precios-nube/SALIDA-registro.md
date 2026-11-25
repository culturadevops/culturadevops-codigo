# SALIDA — el registro de imágenes de contenedor en 4 nubes

Generado 2026-10-14 15:20 UTC con `python registro.py`. Precios de lista en USD, sin impuestos. Solo almacenamiento; descargar en la misma región se trata aparte (ver el vídeo).

## Las tarifas

```
AWS ECR            0.1 por GB al mes   (lista us-east-1 2026-09-11T12:44:25Z)
Azure ACR          Basic 0.1666/día (5.07/mes) con 10 GiB · Standard 0.6666/día (20.28/mes) con 100 GiB · Premium 1.6666/día (50.69/mes) con 500 GiB · GB extra 0.1/mes
                   réplica en otra región (Premium): 1.6666/día (50.69/mes)
Google Artifact R. 0.5 GB gratis, después 0.1000 por GiB al mes
Oracle OCIR        «Container Image Storage: Same as Object Storage - Standard» → 10 GB gratis, después 0.0255 por GB al mes
```

## 5 GB de imágenes guardadas

```
Oracle OCIR                      0.00 USD/mes
Google Artifact Registry         0.45 USD/mes
AWS ECR                          0.50 USD/mes
Azure ACR Basic                  5.07 USD/mes
Azure ACR Standard              20.28 USD/mes
Azure ACR Premium               50.69 USD/mes
```

## 50 GB de imágenes guardadas

```
Oracle OCIR                      1.02 USD/mes
Google Artifact Registry         4.95 USD/mes
AWS ECR                          5.00 USD/mes
Azure ACR Basic                  9.07 USD/mes
Azure ACR Standard              20.28 USD/mes
Azure ACR Premium               50.69 USD/mes
```

## 500 GB de imágenes guardadas

```
Oracle OCIR                     12.49 USD/mes
Google Artifact Registry        49.95 USD/mes
AWS ECR                         50.00 USD/mes
Azure ACR Premium               50.69 USD/mes
Azure ACR Basic                 54.07 USD/mes
Azure ACR Standard              60.28 USD/mes
```

## 2,000 GB de imágenes guardadas

```
Oracle OCIR                     50.74 USD/mes
Google Artifact Registry       199.95 USD/mes
AWS ECR                        200.00 USD/mes
Azure ACR Premium              200.69 USD/mes
Azure ACR Basic                204.07 USD/mes
Azure ACR Standard             210.28 USD/mes
```

## Sin limpieza: 20 builds al día de 300 MB (6 GB al día), lo guardado y lo que cuesta ese mes

```
mes  1:   180 GB → AWS   18.00 · Google   17.95 · Azure Standard   28.28 · Oracle   4.33 USD
mes  3:   540 GB → AWS   54.00 · Google   53.95 · Azure Standard   64.28 · Oracle  13.51 USD
mes  6: 1,080 GB → AWS  108.00 · Google  107.95 · Azure Standard  118.28 · Oracle  27.28 USD
mes 12: 2,160 GB → AWS  216.00 · Google  215.95 · Azure Standard  226.28 · Oracle  54.82 USD
con limpieza (solo las últimas 10 imágenes, 3 GB): AWS 0.30 · Google 0.25 · Azure Basic 5.07 · Oracle 0.00 USD
```

## Escanear vulnerabilidades: 600 imágenes nuevas al mes (20 builds al día)

```
Google Artifact Analysis  0.26/escaneo · activado por defecto en repositorios nuevos: sí → 156.00 USD/mes
AWS Inspector (ECR)       0.09/primer escaneo + 0.01/re-escaneo → 54.00 USD/mes + re-escaneos
Oracle VSS                «Vulnerability Scanning Service Free»
```
