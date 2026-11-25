# SALIDA — Curso de cloud desde cero · 1 · qué es la nube (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-18 14:26 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Autoservicio bajo demanda: pido almacenamiento y me lo dan al instante

`$ aws s3api create-bucket --bucket mi-primer-bucket-cultura`

```
{
    "Location": "/mi-primer-bucket-cultura"
}
```

`$ aws s3 cp hola.txt s3://mi-primer-bucket-cultura/hola.txt`

```
Completed 11 Bytes/11 Bytes (261 Bytes/s) with 1 file(s) remaining
upload: .\hola.txt to s3://mi-primer-bucket-cultura/hola.txt
```

`$ aws s3 ls s3://mi-primer-bucket-cultura/`

```
2026-10-18 09:25:56         11 hola.txt
```

## Elasticidad: tres servidores ahora… y cero un minuto después

`$ aws ec2 run-instances --image-id ami-12c6146b --instance-type t3.micro --count 3 --query Instances[].{Id:InstanceId,Tipo:InstanceType,Estado:State.Name}`

```
[
    {
        "Id": "i-1f35702cba282045e",
        "Tipo": "t3.micro",
        "Estado": "pending"
    },
    {
        "Id": "i-d979639917f535a31",
        "Tipo": "t3.micro",
        "Estado": "pending"
    },
    {
        "Id": "i-a54f24493cd62af3f",
        "Tipo": "t3.micro",
        "Estado": "pending"
    }
]
```

`$ aws ec2 terminate-instances --instance-ids i-1f35702cba282045e i-d979639917f535a31 i-a54f24493cd62af3f --query TerminatingInstances[].CurrentState.Name`

```
[
    "shutting-down",
    "shutting-down",
    "shutting-down"
]
```

> En AWS real, cada una de esas instancias se cobra por segundo mientras existe (mínimo 60 s en Linux).
