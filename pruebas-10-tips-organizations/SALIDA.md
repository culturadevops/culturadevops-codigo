# SALIDA — 10 tips para AWS Organizations (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 00:14 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Una organización creada por la CLI

`$ aws organizations create-organization --feature-set ALL --query Organization.FeatureSet`

```
"ALL"
```

`$ aws organizations enable-policy-type --root-id <raíz> --policy-type SERVICE_CONTROL_POLICY`

```
[
    {
        "Type": "SERVICE_CONTROL_POLICY",
        "Status": "ENABLED"
    }
]
```

`$ aws organizations list-policies-for-target --target-id <raíz> --filter SERVICE_CONTROL_POLICY`

```
[
    "FullAWSAccess"
]
```

## Una OU de pruebas y una cuenta dentro

`$ aws organizations create-organizational-unit --parent-id <raíz> --name pruebas-scp`

```
ou-rcil-6t7s3lxj
```

`$ aws organizations create-account --email dev@example.com --account-name dev --query CreateAccountStatus.AccountId --output text`

```
900205936272
```

`$ aws organizations move-account --account-id <dev> --source-parent-id <raíz> --destination-parent-id <pruebas-scp>`

```
(sin salida)
```

## La SCP que impide salir o cerrar la cuenta

`$ cat no-salir.json`

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "NoSalirNiCerrar",
      "Effect": "Deny",
      "Action": [
        "organizations:LeaveOrganization",
        "account:CloseAccount"
      ],
      "Resource": "*"
    }
  ]
}
```

`$ aws organizations create-policy --name no-salir-ni-cerrar --type SERVICE_CONTROL_POLICY --description Deny Leave y CloseAccount --content file://no-salir.json --query Policy.PolicySummary.Id --output text`

```
p-makifk0f
```

`$ aws organizations attach-policy --policy-id <no-salir-ni-cerrar> --target-id <pruebas-scp>`

```
(sin salida)
```

`$ aws organizations list-policies-for-target --target-id <pruebas-scp> --filter SERVICE_CONTROL_POLICY`

```
[
    "FullAWSAccess",
    "no-salir-ni-cerrar"
]
```

## El tamaño cuenta los espacios

`$ python: len(no-salir.json con sangría) · len(el mismo JSON compacto)`

```
con sangría: 242 caracteres
compacto:    163 caracteres
```
