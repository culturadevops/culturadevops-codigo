# SALIDA — los registros (logs) en 4 nubes

Generado 2026-10-14 14:53 UTC con `python logs.py`. Precios de lista en USD, sin impuestos. Mes = 30 días de ingesta.

## Las tarifas

```
AWS     ingesta Standard 0.5/GB · Infrequent Access 0.25/GB · almacenamiento 0.03/GB-mes · Logs Insights 0.005/GB leído   (lista us-east-1 publicada 2026-10-07T11:55:40Z; sin franja gratis en la lista)
Azure   ingesta 2.3/GB (primeros 5 GB gratis) · 31 días incluidos · retención después 0.1/GB-mes   (Retail Prices API)
        planes más baratos: Basic Logs 0.5/GB · Auxiliary Logs 0.05/GB de ingesta (consultas aparte, por GB leído)
Google  ingesta 0.5/GiB (primeros 50 GiB por proyecto gratis) · 30 días incluidos · retención después 0.01/GiB-mes   (cloud.google.com/stackdriver/pricing)
Oracle  ingesta: sin cobro en la API · «OCI - Logging - Storage» 0 USD hasta 10 GB, después 0.05/GB-mes
```

## 1 GB al día (30 GB/mes), 30 días guardados

```
Google                                0.00 USD/mes
Oracle                                1.00 USD/mes
Azure (Auxiliary, solo ingesta)       1.50 USD/mes
AWS (Infrequent Access)               8.40 USD/mes
Azure (Basic, solo ingesta)          15.00 USD/mes
AWS                                  15.90 USD/mes
Azure (Analytics)                    57.50 USD/mes
```

## 1 GB al día (30 GB/mes), 90 días guardados

```
Google                                0.60 USD/mes
Oracle                                4.00 USD/mes
AWS (Infrequent Access)              10.20 USD/mes
AWS                                  17.70 USD/mes
Azure (Analytics)                    63.40 USD/mes
```

## 10 GB al día (300 GB/mes), 30 días guardados

```
Oracle                               14.50 USD/mes
Azure (Auxiliary, solo ingesta)      15.00 USD/mes
AWS (Infrequent Access)              84.00 USD/mes
Google                              125.00 USD/mes
Azure (Basic, solo ingesta)         150.00 USD/mes
AWS                                 159.00 USD/mes
Azure (Analytics)                   678.50 USD/mes
```

## 10 GB al día (300 GB/mes), 90 días guardados

```
Oracle                               44.50 USD/mes
AWS (Infrequent Access)             102.00 USD/mes
Google                              131.00 USD/mes
AWS                                 177.00 USD/mes
Azure (Analytics)                   737.50 USD/mes
```

## 50 GB al día (1500 GB/mes), 30 días guardados

```
Oracle                               74.50 USD/mes
Azure (Auxiliary, solo ingesta)      75.00 USD/mes
AWS (Infrequent Access)             420.00 USD/mes
Google                              725.00 USD/mes
Azure (Basic, solo ingesta)         750.00 USD/mes
AWS                                 795.00 USD/mes
Azure (Analytics)                  3438.50 USD/mes
```

## 50 GB al día (1500 GB/mes), 90 días guardados

```
Oracle                              224.50 USD/mes
AWS (Infrequent Access)             510.00 USD/mes
Google                              755.00 USD/mes
AWS                                 885.00 USD/mes
Azure (Analytics)                  3733.50 USD/mes
```

## AWS: lo que cuesta leerlos con Logs Insights

```
consultas que leen    10 GB al mes → 0.05 USD
consultas que leen   300 GB al mes → 1.50 USD
consultas que leen  3000 GB al mes → 15.00 USD
```

## AWS, 30 días: lo que ahorras mandando menos

```
10 GB/día, Standard                159.00 USD/mes
5 GB/día (la mitad), Standard       79.50 USD/mes
5 GB/día, Infrequent Access         42.00 USD/mes
```

## AWS: registros que generan sus propios servicios (vended), por tramos

```
$0.50 per GB for the first 10TB
$0.25 per GB for the next 20TB
$0.10 per GB for the next 20TB
$0.05 per GB for over 50TB
```

## Google: el bucket _Required

```
retención fija: 400 días · sin cobro de almacenamiento: sí
```
