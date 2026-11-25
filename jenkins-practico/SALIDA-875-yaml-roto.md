# SALIDA 875 (complemento) — arrancar desde cero con el YAML roto

> Corrida del 2026-11-18 11:54. Misma imagen jk-a-jenkins:1; jenkins.yaml con numExecutors → numExecutor.

```
$ docker run -d --name jk-a-jenkins ... (YAML con numExecutor)
$ docker ps -a --filter name=jk-a-jenkins
exited (exit 5) · 4 s después de arrancar · último /login: 503
$ docker logs jk-a-jenkins | grep -E 'SEVERE|numExecutor' | head -3
2026-11-18 16:54:13.673+0000 [id=90]	SEVERE	jenkins.InitReactorRunner$1#onTaskFailed: Failed ConfigurationAsCode.init
io.jenkins.plugins.casc.UnknownAttributesException: jenkins: Invalid configuration elements for type: class jenkins.model.Jenkins : numExecutor.
[LF]> Available attributes : authorizationStrategy, clouds, crumbIssuer, disableRememberMe, disabledAdministrativeMonitors, globalNodeProperties, labelAtoms, labelString, log, markupFormatter, mode, noUsageStatistics, nodeMonitors
```

## Tamaño del YAML escrito a mano (corrida del 2026-11-18 11:54)

```
$ wc -l 875/jenkins.yaml
89 875/jenkins.yaml
$ grep -c "" 875/estado.groovy
16
```
