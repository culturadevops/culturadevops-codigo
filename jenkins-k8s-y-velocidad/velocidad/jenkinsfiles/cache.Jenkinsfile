// 878 · CACHÉ: lo mismo que la base, con el repositorio local de Maven en un volumen que sobrevive al build.
pipeline {
  agent { docker { image 'maven:3.9.11-eclipse-temurin-21'; args '-v jk-b-m2:/root/.m2' } }
  stages {
    stage('Compilar')   { steps { sh 'mvn -B compile' } }
    stage('Pruebas')    { steps { sh "mvn -B test -Dtest='!PostgresIntegrationTests,!MySqlIntegrationTests'" } }
    stage('Empaquetar') { steps { sh 'mvn -B package -DskipTests' } }
  }
  post {
    always { deleteDir() }
  }
}
