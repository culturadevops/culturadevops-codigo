$ curl -s localhost:8080/api/json | grep version   # Jenkins en Docker, solo local
X-Jenkins: 2.580.1

$ cat Jenkinsfile   # típico de lo que genera una IA
pipeline {
    agent any
    options {
        retryOnFailure(3)
    }
    stages {
        stage('Test') {
            steps {
                sh 'python3 -m pytest'
            }
        }
        stage('Deploy') {
            when { branch 'main' }
            runOn 'produccion'
            steps {
                sh './deploy.sh'
            }
        }
    }
}
$ curl -X POST -F "jenkinsfile=<Jenkinsfile" localhost:8080/pipeline-model-converter/validate
Errors encountered validating Jenkinsfile:
WorkflowScript: 12: Unknown stage section "runOn". Starting with version 0.5, steps in a stage must be in a ‘steps’ block. @ line 12, column 9.
           stage('Deploy') {
           ^

WorkflowScript: 4: Invalid option type "retryOnFailure". Valid option types: [buildDiscarder, catchError, checkoutToSubdirectory, disableConcurrentBuilds, disableRestartFromStage, disableResume, durabilityHint, overrideIndexTriggers, parallelsAlwaysFailFast, preserveStashes, quietPeriod, rateLimitBuilds, retry, script, skipDefaultCheckout, skipStagesAfterUnstable, timeout, waitUntil, warnError, withContext, withCredentials, withEnv, wrap, ws] @ line 4, column 9.
           retryOnFailure(3)
           ^



$ # versión revisada: «retryOnFailure» no existe (la opción se llama retry) y «runOn» tampoco
$ curl -X POST -F "jenkinsfile=<Jenkinsfile" localhost:8080/pipeline-model-converter/validate
Jenkinsfile successfully validated.


$ # se crea el trabajo «demo» con el Jenkinsfile revisado y se ejecuta
$ curl localhost:8080/job/demo/1/consoleText
+ echo pruebas: 12 pasaron
pruebas: 12 pasaron
+ echo versión 1 lista
+ cat version.txt
versión 1 lista
Finished: SUCCESS
