# SALIDA extra — versionado de S3 (vídeo 413)

Generado 2026-10-13 22:12 UTC con `python correr_extra.py`. CLI oficial contra moto; moto no es AWS.

### activar el versionado

`$ aws s3api put-bucket-versioning --bucket contratos --versioning-configuration Status=Enabled`

```

```
(código de salida 0)

### alguien lo pisa con un borrador, y luego lo borra

`$ aws s3 cp v2.txt s3://contratos/contrato.txt; aws s3 rm s3://contratos/contrato.txt`

```
delete: s3://contratos/contrato.txt
```
(código de salida 0)

### ¿está?

`$ aws s3 ls s3://contratos/`

```

```
(código de salida 0)

### las versiones que guarda

`$ aws s3api list-object-versions --bucket contratos`

```
versión  2e803af3…  19 bytes
versión  e3d763b1…  29 bytes
marca de borrado  07286f1a…  (la más reciente)
```

### recuperar la primera versión

`$ aws s3api get-object --bucket contratos --key contrato.txt --version-id … recuperado.txt`

```
29
```
(código de salida 0)

### su contenido

`$ cat recuperado.txt`

```
contrato firmado: 1.000 USD
```
(código de salida 0)
