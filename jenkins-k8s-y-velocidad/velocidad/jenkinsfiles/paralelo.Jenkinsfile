// 878 · PARALELO: las pruebas partidas en dos y el empaquetado, a la vez. Cada rama tiene su propio contenedor y su
// propio workspace (y por eso su propio checkout y su propia descarga de dependencias).
def IMG = 'maven:3.9.11-eclipse-temurin-21'
def GRUPO_B = 'PetClinicIntegrationTests,CrashControllerIntegrationTests,PetClinicConcurrencyTests,ClinicServiceTests'
def GRUPO_A = '!*IntegrationTests,!*ConcurrencyTests,!ClinicServiceTests'
pipeline {
  agent none
  stages {
    stage('Pruebas y paquete') {
      parallel {
        stage('Pruebas A') {
          agent { docker { image IMG } }
          steps { sh "mvn -B test -Dtest='${GRUPO_A}' -Dsurefire.failIfNoSpecifiedTests=false" }
          post { always { deleteDir() } }
        }
        stage('Pruebas B') {
          agent { docker { image IMG } }
          steps { sh "mvn -B test -Dtest='${GRUPO_B}' -Dsurefire.failIfNoSpecifiedTests=false" }
          post { always { deleteDir() } }
        }
        stage('Empaquetar') {
          agent { docker { image IMG } }
          steps { sh 'mvn -B package -DskipTests' }
          post { always { deleteDir() } }
        }
      }
    }
  }
}
