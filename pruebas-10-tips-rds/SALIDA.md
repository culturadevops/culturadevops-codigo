# SALIDA — 10 tips para RDS (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-01 22:59 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Una base creada solo con lo obligatorio

`$ aws rds create-db-instance --db-instance-identifier pruebas --engine postgres --db-instance-class db.t4g.micro --allocated-storage 20 --master-username admin_app --master-user-password ****`

```
"pruebas"
```

`$ aws rds describe-db-instances --db-instance-identifier pruebas --query <valores por defecto>`

```
{
    "BackupRetentionPeriod": 1,
    "DeletionProtection": false,
    "StorageEncrypted": false,
    "PubliclyAccessible": null,
    "StorageType": "gp2",
    "EngineLifecycleSupport": null
}
```

## Protección contra el borrado

`$ aws rds create-db-instance --db-instance-identifier produccion ... --deletion-protection --storage-encrypted --backup-retention-period 14 --no-publicly-accessible`

```
"produccion"
```

`$ aws rds describe-db-instances --db-instance-identifier produccion --query <los mismos campos>`

```
{
    "BackupRetentionPeriod": 14,
    "DeletionProtection": true,
    "StorageEncrypted": true,
    "PubliclyAccessible": false,
    "StorageType": "gp2",
    "EngineLifecycleSupport": null
}
```

`$ aws rds delete-db-instance --db-instance-identifier produccion --skip-final-snapshot`

```
aws: [ERROR]: An error occurred (InvalidParameterCombination) when calling the DeleteDBInstance operation: Cannot delete protected DB Instance, please disable deletion protection and try again.
```

## El snapshot que sobrevive a la base

`$ aws rds create-db-snapshot --db-instance-identifier pruebas --db-snapshot-identifier antes-de-borrar --query DBSnapshot.Status`

```
"available"
```

`$ aws rds delete-db-instance --db-instance-identifier pruebas --skip-final-snapshot --query DBInstance.DBInstanceStatus`

```
"deleting"
```

`$ aws rds describe-db-snapshots --query DBSnapshots[].{Snapshot:DBSnapshotIdentifier,Base:DBInstanceIdentifier,Tipo:SnapshotType,GiB:AllocatedStorage}`

```
[
    {
        "Snapshot": "rds:produccion-2026-10-01-22-59",
        "Base": "produccion",
        "Tipo": "automated",
        "GiB": 20
    },
    {
        "Snapshot": "antes-de-borrar",
        "Base": "pruebas",
        "Tipo": "manual",
        "GiB": 20
    }
]
```
