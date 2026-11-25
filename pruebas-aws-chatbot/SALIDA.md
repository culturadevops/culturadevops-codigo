# SALIDA — AWS Chatbot / Amazon Q Developer in chat applications (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-09 19:55 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS) · región us-east-2
- moto NO emula chatbot ni ejecuta acciones de alarmas; el tramo Slack/Teams no se ejecuta.

## La CLI sigue diciendo chatbot (sin cuenta, sin emulador)

`$ aws chatbot help   # las regiones`

```
* US East (Ohio) - "us-east-2"
* US West (Oregon) - "us-west-2"
* Asia Pacific (Singapore) - "ap-southeast-1"
* Europe (Ireland) - "eu-west-1"

The AWS Chatbot console can only be used in US East (Ohio). Your
configuration data however, is stored in each of the relevant
available Regions.
```

`$ aws chatbot help   # cuántos comandos, y los de Slack`

```
35 comandos
create-slack-channel-configuration
delete-slack-channel-configuration
delete-slack-user-identity
delete-slack-workspace-authorization
describe-slack-channel-configurations
describe-slack-user-identities
describe-slack-workspaces
update-slack-channel-configuration
```

`$ aws chatbot create-slack-channel-configuration --generate-cli-skeleton`

```
{
    "SlackTeamId": "",
    "SlackChannelId": "",
    "SlackChannelName": "",
    "SnsTopicArns": [
        ""
    ],
    "IamRoleArn": "",
    "ConfigurationName": "",
    "LoggingLevel": "",
    "GuardrailPolicyArns": [
        ""
    ],
    "UserAuthorizationRequired": true,
    "Tags": [
        {
            "TagKey": "",
            "TagValue": ""
        }
    ]
}
```

## Alarma de CloudWatch → tema SNS (contra moto)

`$ aws sns create-topic --name alertas-produccion --query TopicArn --output text`

```
arn:aws:sns:us-east-2:123456789012:alertas-produccion
```

`$ aws cloudwatch put-metric-alarm --alarm-name cpu-alta --metric-name CPUUtilization --threshold 80 ... --alarm-actions <tema alertas-produccion>`

```
(sin salida)
```

`$ aws cloudwatch describe-alarms --alarm-names cpu-alta --query MetricAlarms[0].{Alarma:AlarmName,Umbral:Threshold,Acciones:AlarmActions}`

```
{
    "Alarma": "cpu-alta",
    "Umbral": 80.0,
    "Acciones": [
        "arn:aws:sns:us-east-2:123456789012:alertas-produccion"
    ]
}
```

> Lo que pasa cuando la alarma dispara (publicar en el tema y que Chatbot lo lleve al canal) lo hace AWS; moto no ejecuta las acciones de una alarma.

## Notificaciones personalizadas: el validador

`$ cat ejemplos/minima.json`

```
{
  "version": "1.0",
  "source": "custom",
  "content": {
    "description": ":warning: Falló el despliegue de *pagos*"
  }
}
```

`$ cat ejemplos/completa.json`

```
{
  "version": "1.0",
  "source": "custom",
  "id": "despliegue-pagos-42",
  "content": {
    "textType": "client-markdown",
    "title": ":rotating_light: pagos no responde",
    "description": "El servicio *pagos* devuelve 5xx desde las 12:03.",
    "nextSteps": [
      "Revisar el runbook de pagos",
      "Si sigue en 30 min, escalar a guardia"
    ],
    "keywords": [
      "pagos",
      "critico",
      "SRE"
    ]
  },
  "metadata": {
    "threadId": "incidente-pagos-42",
    "summary": "Incidente de pagos",
    "additionalContext": {
      "prioridad": "alta"
    },
    "enableCustomActions": true
  }
}
```

`$ python validar_notificacion.py ejemplos/*.json`

```
ejemplos/minima.json: OK
ejemplos/completa.json: OK
ejemplos/source_aws.json: RECHAZADA
  - source debe ser "custom"
ejemplos/titulo_largo.json: RECHAZADA
  - title: 300 caracteres (máximo 250)
ejemplos/sin_description.json: RECHAZADA
  - content.description es obligatorio
```

## Publicar en SNS y ver lo que llega (cola espía, contra moto)

`$ aws sns subscribe --topic-arn <alertas-produccion> --protocol sqs --notification-endpoint <cola espia> --attributes RawMessageDelivery=true`

```
"arn:aws:sns:us-east-2:123456789012:alertas-produccion:c0304d8c-7ad2-4760-9cfd-f19c87c1a33c"
```

`$ aws sns publish --topic-arn <alertas-produccion> --message file://ejemplos/completa.json`

```
"313fe541-f45c-49ba-9ed9-bf5d5a73863c"
```

`$ aws sqs receive-message --queue-url <espia>   # y se compara con el archivo`

```
threadId: incidente-pagos-42
title:    :rotating_light: pagos no responde
idéntico a ejemplos/completa.json: sí
```

## EventBridge + input transformer → formato de Chatbot (contra moto)

`$ aws events put-rule --name despliegues --event-pattern {"source":["mi.app"],"detail-type":["despliegue"]} --query RuleArn`

```
"arn:aws:events:us-east-2:123456789012:rule/despliegues"
```

`$ cat ejemplos/objetivo.json`

```
[
  {
    "Id": "espia",
    "Arn": "arn:aws:sqs:us-east-2:123456789012:espia",
    "InputTransformer": {
      "InputPathsMap": {
        "svc": "$.detail.servicio",
        "ver": "$.detail.version"
      },
      "InputTemplate": "{\"version\":\"1.0\",\"source\":\"custom\",\"content\":{\"description\":\":rocket: <svc> <ver> desplegado\"}}"
    }
  }
]
```

`$ aws events put-targets --rule despliegues --targets file://ejemplos/objetivo.json --query FailedEntryCount`

```
0
```

`$ aws events put-events --entries '[{"Source":"mi.app","DetailType":"despliegue","Detail":"{\"servicio\":\"pagos\",\"version\":\"2.4.1\"}"}]'`

```
0
```

`$ aws sqs receive-message --queue-url <espia>`

```
{"version": "1.0", "source": "custom", "content": {"description": ":rocket: pagos 2.4.1 desplegado"}}
```

> En tu cuenta el destino de la regla es el tema SNS suscrito a Chatbot; aquí es una cola porque moto da un 500 con destino SNS + InputTransformer.

## Preferencias de la cuenta y acciones personalizadas (esqueletos de la CLI)

`$ aws chatbot update-account-preferences --generate-cli-skeleton`

```
{
    "UserAuthorizationRequired": true,
    "TrainingDataCollectionEnabled": true
}
```

`$ aws chatbot create-custom-action --generate-cli-skeleton`

```
{
    "Definition": {
        "CommandText": ""
    },
    "AliasName": "",
    "Attachments": [
        {
            "NotificationType": "",
            "ButtonText": "",
            "Criteria": [
                {
                    "Operator": "HAS_VALUE",
                    "VariableName": "",
                    "Value": ""
                }
            ],
            "Variables": {
                "KeyName": ""
            }
        }
    ],
    "Tags": [
        {
            "TagKey": "",
            "TagValue": ""
        }
    ],
    "ClientToken": "",
    "ActionName": ""
}
```

> ⚠️ Un esqueleto pone `true` o `""` según el TIPO del campo: NO son los valores por defecto. Los valores por defecto se citan de la referencia de la API, no de aquí.
