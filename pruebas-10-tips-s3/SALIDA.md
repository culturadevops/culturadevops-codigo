# SALIDA — 10 tips para S3 (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-01 22:38 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS, en http://127.0.0.1:5088)
- moto emula la API, no la factura: el coste lo dice la documentación de AWS.

## Subidas multiparte incompletas: ocupan y no se ven

`$ aws s3api create-bucket --bucket tips-mpu`

```
{
    "Location": "/tips-mpu"
}
```

`$ aws s3api create-multipart-upload --bucket tips-mpu --key backup.tar --query UploadId --output text`

```
z8H904wXvHLgm8Ak34xABtm3VXwC5APdpXejyej9hafueIQxnJo6gZnA
```

`$ aws s3api upload-part --bucket tips-mpu --key backup.tar --part-number 1 --body parte.bin (5 MiB) --upload-id <id> --query ETag`

```
"\"46e5bdfbb009e615d9c0f0a55803aa64\""
```

`$ aws s3 ls s3://tips-mpu --recursive --summarize`

```
Total Objects: 0
   Total Size: 0
```

`$ aws s3api list-multipart-uploads --bucket tips-mpu --query Uploads[].{Key:Key,Initiated:Initiated}`

```
[
    {
        "Key": "backup.tar",
        "Initiated": "2010-11-10T20:48:33+00:00"
    }
]
```

`$ aws s3api list-parts --bucket tips-mpu --key backup.tar --upload-id <id> --query Parts[].{Part:PartNumber,Size:Size}`

```
[
    {
        "Part": 1,
        "Size": 5242880
    }
]
```

`$ aws s3api put-bucket-lifecycle-configuration --bucket tips-mpu --lifecycle-configuration file://lifecycle-mpu.json`

```
(sin salida)
```

`$ aws s3api get-bucket-lifecycle-configuration --bucket tips-mpu`

```
{
    "TransitionDefaultMinimumObjectSize": "all_storage_classes_128K",
    "Rules": [
        {
            "ID": "limpiar-multiparte",
            "Filter": {
                "Prefix": ""
            },
            "Status": "Enabled",
            "AbortIncompleteMultipartUpload": {
                "DaysAfterInitiation": 7
            }
        }
    ]
}
```

## Con versionado, borrar no borra

`$ aws s3api create-bucket --bucket tips-versiones`

```
{
    "Location": "/tips-versiones"
}
```

`$ aws s3api put-bucket-versioning --bucket tips-versiones --versioning-configuration Status=Enabled`

```
(sin salida)
```

`$ aws s3api put-object --bucket tips-versiones --key informe.csv --body parte.bin (5 MiB) · vez 1`

```
"a40e1972-5aa5-4216-897c-04b0550d0634"
```

`$ aws s3api put-object --bucket tips-versiones --key informe.csv --body parte.bin (5 MiB) · vez 2`

```
"e409f3c7-2057-40cd-902b-da5c5c11f1cc"
```

`$ aws s3api put-object --bucket tips-versiones --key informe.csv --body parte.bin (5 MiB) · vez 3`

```
"6e462ff3-b43a-47c6-bc18-8dd20e6138e3"
```

`$ aws s3 rm s3://tips-versiones/informe.csv`

```
delete: s3://tips-versiones/informe.csv
```

`$ aws s3 ls s3://tips-versiones --recursive --summarize`

```
Total Objects: 0
   Total Size: 0
```

`$ aws s3api list-object-versions --bucket tips-versiones --query {Versiones:Versions[].{Key:Key,Size:Size,IsLatest:IsLatest},MarcasDeBorrado:DeleteMarkers[].{Key:Key,IsLatest:IsLatest}}`

```
{
    "Versiones": [
        {
            "Key": "informe.csv",
            "Size": 5242880,
            "IsLatest": false
        },
        {
            "Key": "informe.csv",
            "Size": 5242880,
            "IsLatest": false
        },
        {
            "Key": "informe.csv",
            "Size": 5242880,
            "IsLatest": false
        }
    ],
    "MarcasDeBorrado": [
        {
            "Key": "informe.csv",
            "IsLatest": true
        }
    ]
}
```

`$ aws s3api put-bucket-lifecycle-configuration --bucket tips-versiones --lifecycle-configuration file://lifecycle-versiones.json`

```
(sin salida)
```

`$ aws s3api get-bucket-lifecycle-configuration --bucket tips-versiones`

```
{
    "TransitionDefaultMinimumObjectSize": "all_storage_classes_128K",
    "Rules": [
        {
            "Expiration": {
                "ExpiredObjectDeleteMarker": true
            },
            "ID": "versiones-viejas",
            "Filter": {
                "Prefix": ""
            },
            "Status": "Enabled",
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 30
            }
        }
    ]
}
```
