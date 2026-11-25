# SALIDA — Postgres gestionado en 4 nubes

Generado 2026-10-14 14:39 UTC con `python postgres.py`. 2 vCPU, 8 GB, 100 GB SSD; mes = 730 h. Precios de lista en USD, sin impuestos.

## Fuentes y región

- AWS RDS · us-east-1 (Virginia) · db.m6i.large · lista oficial publicada 2026-10-06T22:40:50Z
- Azure PostgreSQL Flexible · eastus (Virginia) · General Purpose D2ds v5 · Retail Prices API
- Google Cloud SQL Enterprise · Iowa (us-central1) (región por defecto de su página) · 2 vCPU + 8 GiB
- Oracle OCI Database with PostgreSQL · 1 OCPU (= 2 vCPU) + 8 GB · API de precios. Partes: tarifa PostgreSQL 0.098/OCPU-h + cómputo E5 0.03/OCPU-h + memoria 0.002/GB-h; almacenamiento optimizado 0.072 + bloque 0.0255 USD/GB-mes

## Un servidor (sin alta disponibilidad)

```
nube      USD/hora  cómputo/mes  disco/mes  TOTAL/mes
Oracle      0.1440       105.12       9.75     114.87
Google      0.1386       101.18      17.00     118.18
AWS         0.1780       129.94      11.50     141.44
Azure       0.1780       129.94      11.50     141.44
```
más barato: Oracle · más caro: AWS y Azure (empate) · diferencia 26.57 USD/mes (23 % más)

## Con alta disponibilidad (réplica en espera)

```
nube      USD/hora  cómputo/mes  disco/mes  TOTAL/mes
Oracle      0.2880       210.24       9.75     219.99
Google      0.2772       202.36      34.00     236.36
AWS         0.3560       259.88      23.00     282.88
Azure       0.3560       259.88      23.00     282.88
```
más barato: Oracle · más caro: AWS y Azure (empate) · diferencia 62.89 USD/mes (29 % más)

## Con compromiso de 1 año (solo el cómputo, por hora)

```
AWS     reserva 1 año sin pago inicial      0.1140  (a demanda 0.1780, -36 %)
Azure   reserva 1 año (por vCore, ÷8.760 h) 0.1068  (a demanda 0.1780, -40 %)
Google  compromiso de uso 1 año             0.1040  (a demanda 0.1386, -25 %)
Oracle  sin precio de compromiso en la API  —
```

## Total al mes con compromiso de 1 año (un servidor, cómputo + disco; Oracle a demanda)

```
Azure       89.50
Google      92.88
AWS         94.72
Oracle     114.87
```

## Otro tamaño: 4 vCPU, 16 GB y 500 GB de disco (un servidor, a demanda)

```
nube                          USD/hora  cómputo/mes  disco/mes  TOTAL/mes
Oracle · 2 OCPU + 16 GB         0.2880       210.24      48.75     258.99
Google · 4 vCPU + 16 GiB        0.2772       202.36      85.00     287.36
AWS · db.m6i.xlarge             0.3560       259.88      57.50     317.38
Azure · D4ds v5 (4 vCore)       0.3560       259.88      57.50     317.38
```

## AWS: las formas de reservar db.m6i.large (pago inicial + por hora → equivale a)

```
1yr All Upfront      inicial     932 USD + 0.0000/h  →   77.67 USD/mes
1yr No Upfront       inicial       0 USD + 0.1140/h  →   83.22 USD/mes
1yr Partial Upfront  inicial     476 USD + 0.0543/h  →   79.31 USD/mes
3yr All Upfront      inicial    1880 USD + 0.0000/h  →   52.22 USD/mes
3yr Partial Upfront  inicial     959 USD + 0.0365/h  →   53.28 USD/mes
a demanda                                         →  129.94 USD/mes
```

## AWS RDS Extended Support (Postgres que ya no tiene soporte normal)

```
Year 1, Year 2  0.10 USD por vCPU-hora · versiones 10, 11, 12, 13 → 2 vCPU: 146.00 USD/mes extra
Year 3          0.20 USD por vCPU-hora · versiones 10, 11, 12, 13 → 2 vCPU: 292.00 USD/mes extra
el servidor db.m6i.large a demanda: 129.94 USD/mes
```
