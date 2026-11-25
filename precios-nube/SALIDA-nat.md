# SALIDA — el NAT Gateway en 4 nubes

Generado 2026-10-14 14:45 UTC con `python nat.py`. Mes = 730 h. Precios de lista en USD, sin impuestos.

## Las tarifas

```
AWS     NAT 0.045/h + 0.045/GB procesado + IPv4 pública 0.005/h   (lista EC2 us-east-1 publicada 2026-10-12T19:39:25Z)
Azure   NAT 0.045/h + 0.045/GB procesado + IP Standard 0.005/h   (Retail Prices API)
Google  0.0014/h por máquina (hasta 32; desde 33: 0.044/h fijo) + 0.045/GiB + IP 0.005/h   (cloud.google.com/nat/pricing)
Oracle  menciones de «NAT» en su lista de precios: 0 · salida a internet 10 TB/mes gratis: sí
```

## 3 máquinas privadas, 1 IP, 100 GB al mes por el NAT

```
nube      pasarela     datos      IP  TOTAL/mes
Oracle        0.00      0.00    0.00       0.00
Google        3.07      4.50    3.65      11.22
AWS          32.85      4.50    3.65      41.00
Azure        32.85      4.50    3.65      41.00
```

## 3 máquinas privadas, 1 IP, 1000 GB al mes por el NAT

```
nube      pasarela     datos      IP  TOTAL/mes
Oracle        0.00      0.00    0.00       0.00
Google        3.07     45.00    3.65      51.72
AWS          32.85     45.00    3.65      81.50
Azure        32.85     45.00    3.65      81.50
```

## 3 máquinas privadas, 1 IP, 5000 GB al mes por el NAT

```
nube      pasarela     datos      IP  TOTAL/mes
Oracle        0.00      0.00    0.00       0.00
Google        3.07    225.00    3.65     231.72
AWS          32.85    225.00    3.65     261.50
Azure        32.85    225.00    3.65     261.50
```

## Google con muchas máquinas: el cobro por máquina tiene tope

```
  1 máquinas → pasarela   1.02 USD/mes
  3 máquinas → pasarela   3.07 USD/mes
 10 máquinas → pasarela  10.22 USD/mes
 32 máquinas → pasarela  32.70 USD/mes
 33 máquinas → pasarela  32.12 USD/mes
100 máquinas → pasarela  32.12 USD/mes
AWS y Azure, cualquier número de máquinas → 32.85 USD/mes por pasarela
```

## AWS: cómo se llama cada cobro del NAT en la factura (usageType)

```
NatGateway-Bytes                 $0.045 per GB Data Processed by NAT Gateways
NatGateway-Hours                 $0.045 per NAT Gateway Hour
NatGateway-Prvd-Bytes            $0.00 per GB Data Processed by NAT Gateways with Provisioned B
NatGateway-Prvd-Gbps             $1.076 per Gbps-hour of NAT Gateways with Provisioned Bandwidt
RegionalNatGateway-Hours         Hourly charge for Regional NAT Gateways
USE1-RegionalNatGateway-Bytes    Charge for per GB data processed by NAT Gateways
```

## AWS: NAT con ancho de banda reservado (0 USD por GB procesado)

```
1.076 USD por Gbps-hora → 1 Gbps reservado: 785.48 USD/mes
punto de equilibrio con el NAT normal: 17,455 GB al mes (17.5 TB)
```

## AWS: un NAT hecho con una máquina t4g.nano (la mantienes tú)

```
t4g.nano Linux a demanda 0.0042/h → 3.07 USD/mes + IPv4 3.65 = 6.72 USD/mes, sin cobro por GB procesado
  100 GB/mes → NAT gestionado   41.00 · máquina propia   6.72 USD/mes
 1000 GB/mes → NAT gestionado   81.50 · máquina propia   6.72 USD/mes
 5000 GB/mes → NAT gestionado  261.50 · máquina propia   6.72 USD/mes
```
