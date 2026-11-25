# SALIDA — 10 tips para Amazon EBS y EFS (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 18:18 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Un volumen creado con la CLI, solo con lo obligatorio

`$ aws ec2 create-volume --availability-zone us-east-1a --size 100
$ aws ec2 describe-volumes --volume-ids <vol>`

```
{
    "Tipo": "gp2",
    "GiB": 100,
    "Cifrado": false
}
```

## Cifrado por defecto

`$ aws ec2 get-ebs-encryption-by-default`

```
{
    "EbsEncryptionByDefault": false
}
```

`$ aws ec2 enable-ebs-encryption-by-default`

```
{
    "EbsEncryptionByDefault": true
}
```

## De gp2 a gp3 sin desmontar nada

`$ aws ec2 modify-volume --volume-id <vol1> --volume-type gp3`

```
{
    "Original": "gp2",
    "Destino": "gp3",
    "Estado": "completed"
}
```

`$ aws ec2 describe-volumes --volume-ids <vol1> --query Volumes[0].VolumeType`

```
"gp3"
```

## Instantáneas

`$ aws ec2 create-snapshot --volume-id <vol1> --description antes-de-actualizar
$ aws ec2 describe-snapshots --snapshot-ids <snap>`

```
{
    "Volumen": true,
    "Desc": "antes-de-actualizar",
    "Estado": "completed",
    "Cifrada": false
}
```

`$ aws ec2 modify-snapshot-tier --snapshot-id <snap> --storage-tier archive`

```
{
    "SnapshotId": "snap-d3d42b8eb607dfdf3",
    "TieringStartTime": "2026-10-10T18:18:40+00:00"
}
```

## Los volúmenes huérfanos

`$ aws ec2 describe-volumes --filters Name=status,Values=available`

```
[
    {
        "Id": "vol-0777e4441bb87c641",
        "GiB": 100,
        "Tipo": "gp3"
    }
]
```

## EFS: un sistema de ficheros creado con la CLI

`$ aws efs create-file-system --creation-token compartido
$ aws efs describe-file-systems --file-system-id <fs>`

```
{
    "Cifrado": false,
    "Rendimiento": "generalPurpose",
    "Throughput": "bursting"
}
```

`$ aws efs describe-lifecycle-configuration --file-system-id <fs>`

```
{
    "LifecyclePolicies": []
}
```

`$ aws efs put-lifecycle-configuration --file-system-id <fs> --lifecycle-policies IA 30 días · Archive 90 · vuelve al primer acceso`

```
{
    "LifecyclePolicies": [
        {
            "TransitionToIA": "AFTER_30_DAYS"
        },
        {
            "TransitionToArchive": "AFTER_90_DAYS"
        },
        {
            "TransitionToPrimaryStorageClass": "AFTER_1_ACCESS"
        }
    ]
}
```

`$ aws efs create-file-system --creation-token cifrado --encrypted`

```
{
    "Cifrado": true
}
```
