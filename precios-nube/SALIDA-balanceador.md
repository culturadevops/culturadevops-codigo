# SALIDA — el balanceador de carga HTTP en 4 nubes

Generado 2026-10-14 15:13 UTC con `python balanceador.py`. Un balanceador, 730 h. Precios de lista en USD, sin impuestos.

## Las tarifas

```
AWS ALB              0.0225/h + 0.008 por LCU-hora (1 LCU = 1 GB/h procesado, entre otras)   (lista us-east-1 2026-09-11T12:45:44Z)
Azure App GW Basic v2 0.0225/h + 0.008 por CU-hora (1 CU = 1 GB/h; hora parcial = entera)
Azure App GW Std v2   0.2/h + 0.008 por CU-hora
Google App LB        primeras 5 reglas 0.025/h (+0.01/h cada una más) + 0.008/GiB entrada + 0.008/GiB salida
Oracle Flexible LB   base: 744 h/mes gratis, después 0.0113/h · ancho de banda: 7,440 Mbps-hora gratis, después 0.0001/Mbps-hora · sin cobro por datos
```

## Sin tráfico: lo que cuesta solo tenerlo encendido

```
Oracle Flexible LB (el primero)        0.00 USD/mes
AWS ALB                               16.43 USD/mes
Azure App GW Basic v2                 16.43 USD/mes
Google App LB                         18.25 USD/mes
Azure App GW Standard v2             146.00 USD/mes
```

## 100 GB procesados al mes

```
Oracle Flexible LB (10 Mbps)           0.00 USD/mes
AWS ALB                               17.23 USD/mes
Google App LB                         19.05 USD/mes
Azure App GW Basic v2                 22.27 USD/mes
Azure App GW Standard v2             151.84 USD/mes
```

## 1,000 GB procesados al mes

```
Oracle Flexible LB (10 Mbps)           0.00 USD/mes
AWS ALB                               24.43 USD/mes
Google App LB                         26.25 USD/mes
Azure App GW Basic v2                 28.11 USD/mes
Azure App GW Standard v2             157.68 USD/mes
```

## 10,000 GB procesados al mes

```
Oracle Flexible LB (100 Mbps)          6.56 USD/mes
AWS ALB                               96.42 USD/mes
Azure App GW Basic v2                 98.19 USD/mes
Google App LB                         98.25 USD/mes
Azure App GW Standard v2             227.76 USD/mes
```

## 50,000 GB procesados al mes

```
Oracle Flexible LB (460 Mbps)         32.84 USD/mes
AWS ALB                              416.43 USD/mes
Google App LB                        418.25 USD/mes
Azure App GW Basic v2                419.39 USD/mes
Azure App GW Standard v2             548.96 USD/mes
```

## Tres balanceadores (un entorno de pruebas, otro de staging y producción), sin apenas tráfico

```
Oracle Flexible LB (3 × 10 Mbps)      17.94 USD/mes
AWS ALB                               49.28 USD/mes
Azure App GW Basic v2                 49.28 USD/mes
Google App LB                         54.75 USD/mes
```

## Capa 4 (balanceador de red): las tarifas

```
AWS NLB          0.0225/h + 0.006 por NLCU-hora (1 NLCU = 1 GB/h, 800 conexiones nuevas/s o 100.000 activas)
Azure LB Std     0.025/h (primeras 5 reglas) + 0.005/GB procesado
Google           mismas tarifas: 0.025/h + 0.008/GiB entrada y 0.008/GiB salida
Oracle NLB       «Flexible Network Load Balancer Free» en su lista de precios
```

## Capa 4, 1,000 GB al mes

```
Oracle NLB                             0.00 USD/mes
AWS NLB                               22.43 USD/mes
Azure Load Balancer Standard          23.25 USD/mes
Google (passthrough)                  26.25 USD/mes
```

## Capa 4, 10,000 GB al mes

```
Oracle NLB                             0.00 USD/mes
Azure Load Balancer Standard          68.25 USD/mes
AWS NLB                               76.42 USD/mes
Google (passthrough)                  98.25 USD/mes
```
