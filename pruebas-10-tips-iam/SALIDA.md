# SALIDA — 10 tips para IAM (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-01 22:54 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- cuentas, fechas e identificadores: los del emulador.

## El resumen de la cuenta: ¿tiene MFA el root?

`$ aws iam get-account-summary --query SummaryMap.{AccountMFAEnabled:AccountMFAEnabled,AccountAccessKeysPresent:AccountAccessKeysPresent,Users:Users}`

```
{
    "AccountMFAEnabled": 0,
    "AccountAccessKeysPresent": 0,
    "Users": 0
}
```

## Claves de acceso que nadie usa

`$ aws iam create-user --user-name ci-antiguo --query User.UserName`

```
"ci-antiguo"
```

`$ aws iam create-access-key --user-name ci-antiguo --query AccessKey.{Usuario:UserName,Estado:Status}`

```
{
    "Usuario": "ci-antiguo",
    "Estado": "Active"
}
```

`$ aws iam generate-credential-report --query State`

```
"STARTED"
```

`$ aws iam get-credential-report  (columnas: user, password_enabled, mfa_active, access_key_1_active, access_key_1_last_used_date)`

```
user,password_enabled,mfa_active,access_key_1_active,access_key_1_last_used_date
ci-antiguo,false,false,true,N/A
```

## Un límite de permisos para delegar

`$ aws iam create-policy --policy-name limite-desarrollo --policy-document file://limite.json --query Policy.PolicyName`

```
"limite-desarrollo"
```

`$ aws iam create-role --role-name rol-de-un-dev --assume-role-policy-document file://confianza.json --permissions-boundary <arn de limite-desarrollo>`

```
"rol-de-un-dev"
```

`$ aws iam get-role --role-name rol-de-un-dev --query Role.PermissionsBoundary`

```
{
    "PermissionsBoundaryType": "PermissionsBoundaryPolicy",
    "PermissionsBoundaryArn": "arn:aws:iam::123456789012:policy/limite-desarrollo"
}
```
