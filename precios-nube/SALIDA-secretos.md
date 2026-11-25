# SALIDA — secretos en 4 nubes

Generado 2026-10-14 14:58 UTC con `python secretos.py`. Precios de lista en USD, sin impuestos.

## Las tarifas

```
AWS Secrets Manager   0.4 por secreto al mes + 0.05 por 10.000 llamadas   (lista us-east-1 2026-09-11T12:46:10Z)
AWS Parameter Store   avanzado 0.05 por parámetro al mes · «$0.05 per 10,000 Advanced Parameter API interaction_Standard…» · líneas de «Standard Parameter» en la lista: 0
AWS KMS               0.03 por 10.000 peticiones (primeras 20,000 al mes gratis) — cada lectura de un SecureString de Parameter Store descifra con KMS
Azure Key Vault       0.03 por 10.000 operaciones · medidores Standard: Advanced Key Operations, Automated Key Rotation, Certificate Renewal Request, Operations, Secret Renewal, Standard Instance
Google Secret Manager versiones activas: 6 gratis, después 8.2192e-05/h (= 0.0600 al mes) · lecturas: 10,000 gratis, después 0.03 por 10.000
Oracle OCI Vault      secretos: Free · claves por software: Free
```

## 20 secretos, 100,000 lecturas al mes

```
AWS Parameter Store (estándar, texto plano)                    0.00 USD/mes
Oracle OCI Vault                                               0.00 USD/mes
AWS Parameter Store (estándar, SecureString + KMS)             0.24 USD/mes
Azure Key Vault                                                0.30 USD/mes
AWS Parameter Store (avanzado + alto rendimiento, sin KMS)     1.02 USD/mes
Google Secret Manager                                          1.11 USD/mes
AWS Secrets Manager                                            8.50 USD/mes
```

## 200 secretos, 10,000,000 lecturas al mes

```
AWS Parameter Store (estándar, texto plano)                    0.00 USD/mes
Oracle OCI Vault                                               0.00 USD/mes
AWS Parameter Store (avanzado + alto rendimiento, sin KMS)    10.22 USD/mes
AWS Parameter Store (estándar, SecureString + KMS)            29.94 USD/mes
Azure Key Vault                                               30.00 USD/mes
Google Secret Manager                                         41.61 USD/mes
AWS Secrets Manager                                          130.00 USD/mes
```

## Lo que cuesta solo TENER los secretos (sin leerlos), al mes

```
   1 secretos → AWS Secrets Manager   0.40 · Google   0.00 · Azure 0.00 · Oracle 0.00
  20 secretos → AWS Secrets Manager   8.00 · Google   0.84 · Azure 0.00 · Oracle 0.00
 200 secretos → AWS Secrets Manager  80.00 · Google  11.64 · Azure 0.00 · Oracle 0.00
```

## Claves de cifrado propias: las tarifas

```
AWS KMS      1.0 por versión de clave al mes + 0.03 por 10.000 operaciones (20,000 gratis)
Azure        claves por software: solo operaciones (0.03 por 10.000) · HSM RSA 2048 (Premium) 1.0 al mes · rotación automática 1.0 por rotación
Google KMS   versión de clave simétrica: software 0.06 · HSM 1.0 · externa 3.0 al mes · operaciones 0.03 por 10.000
Oracle       claves por software: Free · HSM: 20 versiones gratis, después 0.5334 al mes
```

## 10 claves simétricas y 1,000,000 operaciones al mes

```
Oracle Vault (software o HSM, dentro de las 20 gratis)         0.00 USD/mes
Azure Key Vault (claves por software)                          3.00 USD/mes
Google Cloud KMS (software)                                    3.60 USD/mes
AWS KMS                                                       12.94 USD/mes
```

## Un HSM dedicado para ti solo (cuando el cumplimiento lo exige)

```
Oracle  bóveda privada virtual   3.724/h → 2,718.52 USD/mes
Azure   Dedicated HSM            4.85/h → 3,540.50 USD/mes
```
