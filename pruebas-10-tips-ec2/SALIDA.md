# SALIDA — 10 tips para EC2 (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-01 22:45 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura: los costos los dice la documentación.

## Un volumen que sobrevive a su instancia

`$ aws ec2 run-instances --image-id <ami> --instance-type t3.micro`

```
i-97bd3437dd14573e6
```

`$ aws ec2 create-volume --availability-zone us-east-1a --size 100 --volume-type gp2 --query VolumeId --output text`

```
vol-d47c99764a5985404
```

`$ aws ec2 attach-volume --volume-id <vol> --instance-id <i> --device /dev/sdf`

```
"attaching"
```

`$ aws ec2 terminate-instances --instance-ids <i>`

```
"shutting-down"
```

`$ aws ec2 describe-volumes --filters Name=status,Values=available --query Volumes[].{Id:VolumeId,GiB:Size,Tipo:VolumeType,Estado:State}`

```
[
    {
        "Id": "vol-d47c99764a5985404",
        "GiB": 100,
        "Tipo": "gp2",
        "Estado": "available"
    }
]
```

## gp2 a gp3 sin parar nada

`$ aws ec2 describe-volumes --filters Name=volume-type,Values=gp2 --query Volumes[].{Id:VolumeId,GiB:Size,Tipo:VolumeType}`

```
[
    {
        "Id": "vol-d47c99764a5985404",
        "GiB": 100,
        "Tipo": "gp2"
    }
]
```

`$ aws ec2 modify-volume --volume-id <vol> --volume-type gp3`

```
{
    "De": "gp2",
    "A": "gp3",
    "Estado": "completed"
}
```

## Una IP elástica sin asociar

`$ aws ec2 allocate-address --domain vpc --query PublicIp --output text`

```
127.4.75.7
```

`$ aws ec2 describe-addresses --query Addresses[?AssociationId==null].{IP:PublicIp,Asociada:AssociationId}`

```
[
    {
        "IP": "127.4.75.7",
        "Asociada": null
    }
]
```

## IMDSv2 obligatorio al lanzar

`$ aws ec2 run-instances --image-id <ami> --instance-type t3.micro --metadata-options HttpEndpoint=enabled,HttpTokens=required,HttpPutResponseHopLimit=2`

```
i-1abde2400e2362719
```

`$ aws ec2 describe-instances --instance-ids <i> --query ...MetadataOptions`

```
{
    "HttpTokens": "required",
    "Hops": 2
}
```

## Cifrado de EBS por defecto (por región)

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

`$ aws ec2 get-ebs-encryption-by-default`

```
{
    "EbsEncryptionByDefault": true
}
```
