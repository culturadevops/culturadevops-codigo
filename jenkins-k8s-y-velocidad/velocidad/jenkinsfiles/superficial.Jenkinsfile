// 878 · CHECKOUT SUPERFICIAL: sin el checkout por defecto; uno propio con un solo commit y sin etiquetas.
pipeline {
  agent { docker { image 'maven:3.9.11-eclipse-temurin-21' } }
  options { skipDefaultCheckout() }
  stages {
    stage('Checkout') {
      steps {
        checkout scmGit(branches: [[name: 'banco']], userRemoteConfigs: [[url: 'file:///repos/petclinic.git']],
                        extensions: [cloneOption(shallow: true, depth: 1, noTags: true, reference: '', timeout: 10)])
      }
    }
    stage('Compilar')   { steps { sh 'mvn -B compile' } }
    stage('Pruebas')    { steps { sh "mvn -B test -Dtest='!PostgresIntegrationTests,!MySqlIntegrationTests'" } }
    stage('Empaquetar') { steps { sh 'mvn -B package -DskipTests' } }
  }
  post {
    always { deleteDir() }
  }
}
