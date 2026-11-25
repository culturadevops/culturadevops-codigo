# SALIDA · 706 · Terraform escrito por IA: pasa validate y suspende Checkov

Generado por `ejecutar_todo.py` el 2026-10-29. Sin cuenta de AWS: solo `terraform init -backend=false` + `terraform validate`, Checkov y `trivy config`, todo en Docker con `--rm`.

## Versiones

- Terraform v1.16.7 (imagen hashicorp/terraform:1.16.7) · Checkov 3.3.30 (bridgecrew/checkov:3.3.30) · Trivy Version: 0.76.1 (aquasec/trivy:0.76.1)
- Modelo local: `qwen2.5:7b` digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` vía Ollama `/api/chat`, opciones {"temperature": 0.7, "top_p": 0.9, "num_ctx": 8192} + `seed` 1 y 2.
- Claude Code 2.1.312, `claude -p --safe-mode --tools "" --output-format json --no-session-persistence --max-budget-usd 1`, desde un directorio temporal vacío y sin variables de credenciales. Modelo que respondió: `claude-opus-5-5`. La temperatura de Claude Code no se puede fijar: una sola muestra por petición. `--bare` no se usó porque exige ANTHROPIC_API_KEY y la cuenta es OAuth; `--safe-mode` desactiva CLAUDE.md, hooks, MCP y skills.
- Versión del proveedor aws que eligió cada módulo (la escribe la IA en required_providers): {'4.67.0': 45, '-': 5, '5.100.0': 21, '6.71.0': 4}
  - qwen-s1: {'4.67.0': 23, '-': 2}
  - qwen-s2: {'4.67.0': 22, '-': 3}
  - claude: {'5.100.0': 21, '6.71.0': 4}
- Última versión del proveedor aws en el Registry hoy: 6.71.0 (publicada 2026-10-28).

## Prompt (igual para las dos IA)

```
Escribe el código de Terraform para {pedido} en AWS (región us-east-1). Responde solo con el archivo main.tf completo, incluidos los bloques terraform/required_providers y provider, en un único bloque ```hcl.
```

Bucle (rondas 1-3), a cada módulo con fallas:

```
Este es tu main.tf:

```hcl
{codigo}
```

Checkov reporta estas fallas:
{fallas}

Corrige el código para que Checkov no reporte fallas. Responde solo con el main.tf completo en un único bloque ```hcl.
```

## Criterio (fijado antes de generar, peticiones.py)

- 25 peticiones típicas, ninguna menciona la seguridad: s3-backups, s3-web, sg-web, ec2-ubuntu, rds-postgres, rds-mysql, eks, vpc, lambda, dynamodb, sqs, sns, ecr, alb, iam-ci, cloudwatch-logs, redis, efs, apigw-lambda, cloudfront-s3, secrets, kms, bastion, ecs-fargate, cloudtrail.
- «Válido» = init y validate con salida 0. «Limpio» = válido y Checkov sin ninguna falla.
- Se cuentan TODAS las fallas de Checkov (framework terraform) y de trivy config, también las que mucha gente considera ruido (replicación entre regiones, notificaciones de S3…). Checkov y Trivy también escanean los módulos inválidos.
- Categorías por palabras del nombre de la regla, la primera que casa: red abierta (0.0.0.0/0, puertos): 0.0.0.0, ingress, egress, port 22, port 3389, unrestricted, security group, public ip, ssh; acceso público: public, anonymous, acl; cifrado: encrypt, kms, cmk, tls, ssl, https, transit; registro y monitoreo: log, trail, monitor, x-ray, tracing, insights, notification, audit; respaldo y borrado: backup, deletion, versioning, replication, recovery, snapshot, retention, multi-az, multi az, lifecycle, lock; IAM y permisos: iam, policy, privilege, permission, role, authentication, authorizer, imdsv2, metadata; si no, «otras».
- Supresión = `#\s*checkov:skip`, `#\s*trivy:ignore`, `#\s*tfsec:ignore` en el código. Checkov también cuenta las que reconoce (skipped).
- Muestra pequeña (25 peticiones, 50 módulos de qwen y 25 de Claude): esto no es un estudio.

## Ronda 0: lo que sale a la primera

| IA | módulos | init OK | validate OK | limpios (Checkov 0) | fallas Checkov | pasadas | % fallas | trivy FAIL | CRITICAL | HIGH | trivy limpios (válidos) | con 0.0.0.0/0 | supresiones |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen-s1 | 25 | 23 | 11 | 0 | 153 | 178 | 46.2 % | 92 | 7 | 44 | 0 | 9 | 0 |
| qwen-s2 | 25 | 22 | 10 | 0 | 130 | 170 | 43.3 % | 95 | 8 | 38 | 0 | 9 | 0 |
| claude | 25 | 25 | 25 | 2 | 154 | 527 | 22.6 % | 73 | 17 | 21 | 3 | 11 | 0 |

### Fallas de Checkov por categoría (ronda 0)

| categoría | qwen-s1 | qwen-s2 | claude |
|---|---|---|---|
| red abierta (0.0.0.0/0, puertos) | 33 | 26 | 38 |
| acceso público | 10 | 7 | 7 |
| cifrado | 29 | 20 | 28 |
| registro y monitoreo | 26 | 23 | 33 |
| respaldo y borrado | 12 | 15 | 11 |
| IAM y permisos | 15 | 9 | 10 |
| otras | 28 | 30 | 27 |

### Reglas concretas (fallas en ronda 0)

| regla | qué es | qwen-s1 | qwen-s2 | claude |
|---|---|---|---|---|
| CKV_AWS_24 | SSH abierto a 0.0.0.0/0 | 3 | 2 | 1 |
| CKV_AWS_260 | puerto 80 abierto a 0.0.0.0/0 | 4 | 3 | 3 |
| CKV_AWS_382 | salida a 0.0.0.0/0, todos los puertos | 6 | 7 | 8 |
| CKV_AWS_79 | IMDSv1 activo | 6 | 4 | 0 |
| CKV_AWS_8 | disco de EC2 sin cifrar | 4 | 4 | 2 |
| CKV_AWS_27 | SQS sin cifrar | 4 | 0 | 0 |
| CKV2_AWS_6 | S3 sin bloqueo de acceso público | 3 | 4 | 1 |
| CKV_AWS_145 | S3 sin KMS | 3 | 4 | 4 |
| CKV_AWS_16 | RDS sin cifrar | 0 | 0 | 0 |
| CKV_AWS_17 | RDS pública | 0 | 0 | 0 |
| CKV_AWS_144 | S3 sin replicación entre regiones | 3 | 4 | 4 |
| CKV_AWS_18 | S3 sin access logging | 3 | 4 | 4 |
| CKV_AWS_158 | logs de CloudWatch sin KMS | 1 | 1 | 5 |
| CKV_AWS_338 | logs de CloudWatch < 1 año | 1 | 1 | 5 |
| CKV_AWS_88 | EC2 con IP pública | 1 | 0 | 5 |
| CKV_AWS_23 | security group sin descripción | 8 | 7 | 8 |

### Las 10 reglas que más fallan, por IA

- **qwen-s1**: CKV_AWS_23 Ensure every security group and rule has a description ×8; CKV_AWS_79 Ensure Instance Metadata Service Version 1 is not enabled ×6; CKV_AWS_135 Ensure that EC2 is EBS optimized ×6; CKV_AWS_126 Ensure that detailed monitoring is enabled for EC2 instances ×6; CKV2_AWS_41 Ensure an IAM role is attached to EC2 instance ×6; CKV_AWS_382 Ensure no security groups allow egress from 0.0.0.0:0 to port -1 ×6; CKV_AWS_8 Ensure all data stored in the Launch configuration or instance Elastic Blocks Store is securely encrypted ×4; CKV_AWS_260 Ensure no security groups allow ingress from 0.0.0.0:0 to port 80 ×4; CKV2_AWS_12 Ensure the default security group of every VPC restricts all traffic ×4; CKV2_AWS_11 Ensure VPC flow logging is enabled in all VPCs ×4
- **qwen-s2**: CKV_AWS_382 Ensure no security groups allow egress from 0.0.0.0:0 to port -1 ×7; CKV_AWS_23 Ensure every security group and rule has a description ×7; CKV_AWS_79 Ensure Instance Metadata Service Version 1 is not enabled ×4; CKV_AWS_135 Ensure that EC2 is EBS optimized ×4; CKV_AWS_8 Ensure all data stored in the Launch configuration or instance Elastic Blocks Store is securely encrypted ×4; CKV_AWS_126 Ensure that detailed monitoring is enabled for EC2 instances ×4; CKV2_AWS_41 Ensure an IAM role is attached to EC2 instance ×4; CKV2_AWS_12 Ensure the default security group of every VPC restricts all traffic ×4; CKV2_AWS_11 Ensure VPC flow logging is enabled in all VPCs ×4; CKV2_AWS_6 Ensure that S3 bucket has a Public Access block ×4
- **claude**: CKV_AWS_382 Ensure no security groups allow egress from 0.0.0.0:0 to port -1 ×8; CKV_AWS_23 Ensure every security group and rule has a description ×8; CKV_AWS_135 Ensure that EC2 is EBS optimized ×6; CKV_AWS_126 Ensure that detailed monitoring is enabled for EC2 instances ×6; CKV_AWS_88 EC2 instance should not have public IP. ×5; CKV_AWS_158 Ensure that CloudWatch Log Group is encrypted by KMS ×5; CKV_AWS_338 Ensure CloudWatch log groups retains logs for at least 1 year ×5; CKV_AWS_130 Ensure VPC subnets do not assign public IP by default ×5; CKV2_AWS_41 Ensure an IAM role is attached to EC2 instance ×4; CKV2_AWS_12 Ensure the default security group of every VPC restricts all traffic ×4

### Tipos de recurso que no existen (validate: «does not support resource type»)

- qwen-s1: 4 — rds-mysql: `aws_rds_instance` (¿aws_db_instance?); rds-postgres: `aws_rds_cluster_parameter`; rds-postgres: `aws_rds_instance` (¿aws_db_instance?); s3-web: `aws_s3_bucket_website`
- qwen-s2: 5 — rds-mysql: `aws_rds_instance` (¿aws_db_instance?); rds-postgres: `aws_rds_instance` (¿aws_db_instance?); s3-web: `aws_s3_bucket_website`; sqs: `aws_queue`; sqs: `aws_queue_policy`
- claude: 0 — ninguno

### Errores de validate (resumen de Terraform)

- qwen-s1: Unsupported block type ×6; Invalid resource type ×4; Unsupported argument ×3; Attribute redefined ×1; Insufficient vpc_config blocks ×1; Missing attribute separator ×1; Error in function call ×1; Missing required argument ×1; Unsupported attribute ×1; Reference to "count" in non-counted context ×1
- qwen-s2: Invalid resource type ×6; Unsupported attribute ×4; Unsupported block type ×3; Invalid reference ×2; Reference to "count" in non-counted context ×1; Reference to undeclared resource ×1; Invalid block definition ×1; Incorrect attribute value type ×1; Missing key/value separator ×1; Insufficient vpc_config blocks ×1; Unsupported argument ×1; Reference to undeclared input variable ×1; Invalid resource type name ×1
- claude: ninguno

## El bucle IA + Checkov (rondas 0-3)

qwen-s1: los 25 módulos. Claude: muestra fijada antes de mirar = s3-backups, sg-web, rds-postgres, eks, ec2-ubuntu.

| IA | ronda | módulos | validate OK | limpios | fallas Checkov | pasadas | trivy FAIL | `#checkov:skip`/ignore en el código | skipped por Checkov | líneas de código | recursos |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen-s1 | r0 | 25 | 11 | 0 | 153 | 178 | 92 | 0 | 0 | 1331 | 90 |
| qwen-s1 | r1 | 25 | 4 | 0 | 169 | 277 | 101 | 0 | 0 | 2029 | 133 |
| qwen-s1 | r2 | 25 | 2 | 1 | 163 | 364 | 92 | 0 | 0 | 2482 | 159 |
| qwen-s1 | r3 | 25 | 2 | 1 | 173 | 440 | 88 | 0 | 0 | 2903 | 188 |
| claude | r0 | 5 | 5 | 0 | 22 | 150 | 18 | 0 | 0 | 984 | 42 |
| claude | r1 | 5 | 5 | 5 | 0 | 288 | 4 | 7 | 7 | 1955 | 84 |
| claude | r2 | 5 | 5 | 5 | 0 | 288 | 4 | 7 | 7 | 1955 | 84 |
| claude | r3 | 5 | 5 | 5 | 0 | 288 | 4 | 7 | 7 | 1955 | 84 |

### Por módulo en el bucle (fallas Checkov r0→r1→r2→r3; v = validate OK; s = supresiones)

- qwen-s1 s3-backups: 7v → 18✗ → 10✗ → 13✗
- qwen-s1 s3-web: 8✗ → 6✗ → 6✗ → 6✗
- qwen-s1 sg-web: 5v → 8v → 6v → 5v
- qwen-s1 ec2-ubuntu: 5✗ → 2✗ → 3✗ → 3✗
- qwen-s1 rds-postgres: 0✗ → 7✗ → 7✗ → 9✗
- qwen-s1 rds-mysql: 3✗ → 4✗ → 2✗ → 1✗
- qwen-s1 eks: 5✗ → 4✗ → 4✗ → 4✗
- qwen-s1 vpc: 11✗ → 9✗ → 9✗ → 9✗
- qwen-s1 lambda: 5✗ → 3✗ → 5✗ → 5✗
- qwen-s1 dynamodb: 2✗ → 4✗ → 4✗ → 3✗
- qwen-s1 sqs: 7✗ → 7✗ → 7✗ → 7✗
- qwen-s1 sns: 1v → 3✗ → 1✗ → 1✗
- qwen-s1 ecr: 3v → 1✗ → 5✗ → 8✗
- qwen-s1 alb: 20✗ → 17✗ → 24✗ → 24✗
- qwen-s1 iam-ci: 0✗ → 9v → 4✗ → 3✗
- qwen-s1 cloudwatch-logs: 2v → 2v → 0✗ → 0✗
- qwen-s1 redis: 6✗ → 6✗ → 5✗ → 3✗
- qwen-s1 efs: 13v → 0✗ → 10✗ → 13✗
- qwen-s1 apigw-lambda: 4v → 11✗ → 7✗ → 11✗
- qwen-s1 cloudfront-s3: 16✗ → 17✗ → 18✗ → 19✗
- qwen-s1 secrets: 2v → 3✗ → 1✗ → 1✗
- qwen-s1 kms: 2v → 1v → 0v → 0v
- qwen-s1 bastion: 9v → 2✗ → 2✗ → 2✗
- qwen-s1 ecs-fargate: 13✗ → 11✗ → 10✗ → 10✗
- qwen-s1 cloudtrail: 4v → 14✗ → 13✗ → 13✗
- claude s3-backups: 4v → 0vs7 → 0vs7 → 0vs7
- claude sg-web: 2v → 0v → 0v → 0v
- claude rds-postgres: 2v → 0v → 0v → 0v
- claude eks: 9v → 0v → 0v → 0v
- claude ec2-ubuntu: 5v → 0v → 0v → 0v

### Supresiones que metió la IA (líneas del código)

- claude r1 s3-backups:153: `#checkov:skip=CKV_AWS_18:Es el bucket destino de los logs de acceso; registrarse a sí mismo genera un bucle de logs`
- claude r1 s3-backups:154: `#checkov:skip=CKV_AWS_144:Los logs de acceso no requieren replicación entre regiones`
- claude r1 s3-backups:155: `#checkov:skip=CKV2_AWS_62:No se requieren notificaciones de eventos para los logs de acceso`
- claude r1 s3-backups:156: `#checkov:skip=CKV_AWS_145:El logging de acceso de S3 solo admite SSE-S3 en el bucket destino, no SSE-KMS`
- claude r1 s3-backups:292: `#checkov:skip=CKV_AWS_144:Es el bucket destino de la replicación; replicarlo de nuevo no aporta resiliencia adicional`
- claude r1 s3-backups:293: `#checkov:skip=CKV_AWS_18:El bucket de logs debe estar en la misma región; el acceso se audita vía CloudTrail`
- claude r1 s3-backups:294: `#checkov:skip=CKV2_AWS_62:Las notificaciones de eventos se gestionan en el bucket origen`
- claude r2 s3-backups:153: `#checkov:skip=CKV_AWS_18:Es el bucket destino de los logs de acceso; registrarse a sí mismo genera un bucle de logs`
- claude r2 s3-backups:154: `#checkov:skip=CKV_AWS_144:Los logs de acceso no requieren replicación entre regiones`
- claude r2 s3-backups:155: `#checkov:skip=CKV2_AWS_62:No se requieren notificaciones de eventos para los logs de acceso`
- claude r2 s3-backups:156: `#checkov:skip=CKV_AWS_145:El logging de acceso de S3 solo admite SSE-S3 en el bucket destino, no SSE-KMS`
- claude r2 s3-backups:292: `#checkov:skip=CKV_AWS_144:Es el bucket destino de la replicación; replicarlo de nuevo no aporta resiliencia adicional`
- claude r2 s3-backups:293: `#checkov:skip=CKV_AWS_18:El bucket de logs debe estar en la misma región; el acceso se audita vía CloudTrail`
- claude r2 s3-backups:294: `#checkov:skip=CKV2_AWS_62:Las notificaciones de eventos se gestionan en el bucket origen`
- claude r3 s3-backups:153: `#checkov:skip=CKV_AWS_18:Es el bucket destino de los logs de acceso; registrarse a sí mismo genera un bucle de logs`
- claude r3 s3-backups:154: `#checkov:skip=CKV_AWS_144:Los logs de acceso no requieren replicación entre regiones`
- claude r3 s3-backups:155: `#checkov:skip=CKV2_AWS_62:No se requieren notificaciones de eventos para los logs de acceso`
- claude r3 s3-backups:156: `#checkov:skip=CKV_AWS_145:El logging de acceso de S3 solo admite SSE-S3 en el bucket destino, no SSE-KMS`
- claude r3 s3-backups:292: `#checkov:skip=CKV_AWS_144:Es el bucket destino de la replicación; replicarlo de nuevo no aporta resiliencia adicional`
- claude r3 s3-backups:293: `#checkov:skip=CKV_AWS_18:El bucket de logs debe estar en la misma región; el acceso se audita vía CloudTrail`
- claude r3 s3-backups:294: `#checkov:skip=CKV2_AWS_62:Las notificaciones de eventos se gestionan en el bucket origen`

### Claude r0 → r1: qué cambió para que Checkov pase (grep literal)

- s3-backups r0: 162 líneas, 7 recursos · `resource "aws_s3_bucket" "backups" {`
- s3-backups r1: 745 líneas, 32 recursos · `resource "aws_s3_bucket" "logs" {`; `resource "aws_s3_bucket" "replica" {`; `resource "aws_s3_bucket" "backups" {`
- sg-web r0: 116 líneas, 8 recursos · `from_port         = 80`; `from_port         = 80`
- sg-web r1: 130 líneas, 7 recursos · `resource "aws_network_interface" "web" {`
- rds-postgres r0: 330 líneas, 11 recursos · —
- rds-postgres r1: 357 líneas, 11 recursos · —
- eks r0: 227 líneas, 13 recursos · `endpoint_public_access  = true`
- eks r1: 474 líneas, 26 recursos · `endpoint_public_access  = false`
- ec2-ubuntu r0: 149 líneas, 3 recursos · `associate_public_ip_address = true`
- ec2-ubuntu r1: 249 líneas, 8 recursos · `associate_public_ip_address = false`

## Por módulo, ronda 0 (fallas Checkov / trivy; ✗ = no valida)

| petición | qwen-s1 | qwen-s2 | claude |
|---|---|---|---|
| s3-backups | 7 / 8 | 8 / 8 ✗ | 4 / 2 |
| s3-web | 8 / 8 ✗ | 7 / 8 ✗ | 8 / 4 |
| sg-web | 5 / 6 | 5 / 6 | 2 / 2 |
| ec2-ubuntu | 5 / 2 ✗ | 5 / 2 | 5 / 1 |
| rds-postgres | 0 / 0 ✗ | 3 / 3 ✗ | 2 / 2 |
| rds-mysql | 3 / 3 ✗ | 3 / 3 ✗ | 6 / 4 |
| eks | 5 / 8 ✗ | 6 / 8 ✗ | 9 / 11 |
| vpc | 11 / 7 ✗ | 2 / 1 | 4 / 3 |
| lambda | 5 / 1 ✗ | 5 / 1 | 8 / 2 |
| dynamodb | 2 / 2 ✗ | 2 / 2 ✗ | 1 / 1 |
| sqs | 7 / 4 ✗ | 0 / 0 ✗ | 0 / 0 |
| sns | 1 / 1 | 1 / 1 ✗ | 0 / 1 |
| ecr | 3 / 3 | 3 / 3 | 1 / 1 |
| alb | 20 / 8 ✗ | 18 / 9 ✗ | 23 / 9 |
| iam-ci | 0 / 0 ✗ | 8 / 8 | 2 / 1 |
| cloudwatch-logs | 2 / 1 | 2 / 1 | 2 / 1 |
| redis | 6 / 5 ✗ | 4 / 4 ✗ | 3 / 2 |
| efs | 13 / 6 | 2 / 0 ✗ | 10 / 3 |
| apigw-lambda | 4 / 1 | 10 / 2 ✗ | 11 / 3 |
| cloudfront-s3 | 16 / 0 ✗ | 15 / 11 ✗ | 12 / 4 |
| secrets | 2 / 1 | 2 / 1 | 2 / 0 |
| kms | 2 / 1 | 2 / 1 | 3 / 0 |
| bastion | 9 / 6 | 10 / 7 | 8 / 2 |
| ecs-fargate | 13 / 7 ✗ | 7 / 5 ✗ | 20 / 10 |
| cloudtrail | 4 / 3 | 0 / 0 ✗ | 8 / 4 |

## Demos de terminal (texto literal)

### claude · s3-backups

```
$ terraform validate
Success! The configuration is valid.

# exit=0

$ checkov -f main.tf --framework terraform --compact --quiet
terraform scan results:
Passed checks: 26, Failed checks: 4, Skipped checks: 0
Check: CKV2_AWS_62: "Ensure S3 buckets should have event notifications enabled"
	FAILED for resource: aws_s3_bucket.backups
Check: CKV_AWS_144: "Ensure that S3 bucket has cross-region replication enabled"
	FAILED for resource: aws_s3_bucket.backups
Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
	FAILED for resource: aws_s3_bucket.backups
Check: CKV_AWS_145: "Ensure that S3 buckets are encrypted with KMS by default"
	FAILED for resource: aws_s3_bucket.backups
# exit=1
```

### qwen-s1 · sg-web

```
$ terraform validate
Success! The configuration is valid.

# exit=0

$ checkov -f main.tf --framework terraform --compact --quiet
terraform scan results:
Passed checks: 3, Failed checks: 5, Skipped checks: 0
Check: CKV_AWS_382: "Ensure no security groups allow egress from 0.0.0.0:0 to port -1"
	FAILED for resource: aws_security_group.web_server
Check: CKV_AWS_23: "Ensure every security group and rule has a description"
	FAILED for resource: aws_security_group.web_server
Check: CKV_AWS_24: "Ensure no security groups allow ingress from 0.0.0.0:0 to port 22"
	FAILED for resource: aws_security_group.web_server
Check: CKV_AWS_260: "Ensure no security groups allow ingress from 0.0.0.0:0 to port 80"
	FAILED for resource: aws_security_group.web_server
Check: CKV2_AWS_5: "Ensure that Security Groups are attached to another resource"
	FAILED for resource: aws_security_group.web_server
# exit=1
```

### qwen-s1 · rds-postgres

```
$ terraform validate
Error: Invalid resource type

  on main.tf line 14, in resource "aws_rds_instance" "postgres":
  14: resource "aws_rds_instance" "postgres" {

The provider hashicorp/aws does not support resource type "aws_rds_instance".
Did you mean "aws_db_instance"?

Error: Invalid resource type

  on main.tf line 38, in resource "aws_rds_cluster_parameter" "postgres":
  38: resource "aws_rds_cluster_parameter" "postgres" {

The provider hashicorp/aws does not support resource type
"aws_rds_cluster_parameter".
# exit=1

$ checkov -f main.tf --framework terraform --compact --quiet
terraform scan results:
Passed checks: 1, Failed checks: 0, Skipped checks: 0
# exit=0
```

### claude · sg-web

```
$ terraform validate
Success! The configuration is valid.

# exit=0

$ checkov -f main.tf --framework terraform --compact --quiet
terraform scan results:
Passed checks: 35, Failed checks: 2, Skipped checks: 0
Check: CKV_AWS_260: "Ensure no security groups allow ingress from 0.0.0.0:0 to port 80"
	FAILED for resource: aws_vpc_security_group_ingress_rule.http_ipv4
Check: CKV2_AWS_5: "Ensure that Security Groups are attached to another resource"
	FAILED for resource: aws_security_group.web
# exit=1
```

### qwen-s2 · sqs

```
$ terraform validate
Error: Invalid resource type

  on main.tf line 14, in resource "aws_queue" "main_queue":
  14: resource "aws_queue" "main_queue" {

The provider hashicorp/aws does not support resource type "aws_queue".

Error: Invalid resource type

  on main.tf line 18, in resource "aws_queue" "dead_letter_queue":
  18: resource "aws_queue" "dead_letter_queue" {

The provider hashicorp/aws does not support resource type "aws_queue".

Error: Invalid resource type

  on main.tf line 29, in resource "aws_queue_policy" "dead_letter_queue_policy":
  29: resource "aws_queue_policy" "dead_letter_queue_policy" {

The provider hashicorp/aws does not support resource type "aws_queue_policy".
# exit=1

$ checkov -f main.tf --framework terraform --compact --quiet
terraform scan results:
Passed checks: 1, Failed checks: 0, Skipped checks: 0
# exit=0
```

