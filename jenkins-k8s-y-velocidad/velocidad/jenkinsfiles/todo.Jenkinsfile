// 878 · TODO JUNTO: paralelo + imagen de agente preparada + checkout superficial en cada rama.
def IMG = 'jk-b-agente-petclinic:1'
def GRUPO_B = 'PetClinicIntegrationTests,CrashControllerIntegrationTests,PetClinicConcurrencyTests,ClinicServiceTests'
def GRUPO_A = '!*IntegrationTests,!*ConcurrencyTests,!ClinicServiceTests'
def superficial() {
  checkout scmGit(branches: [[name: 'banco']], userRemoteConfigs: [[url: 'file:///repos/petclinic.git']],
                  extensions: [cloneOption(shallow: true, depth: 1, noTags: true, reference: '', timeout: 10)])
}
pipeline {
  agent none
  options { skipDefaultCheckout() }
  stages {
    stage('Pruebas y paquete') {
      parallel {
        stage('Pruebas A') {
          agent { docker { image IMG } }
          steps { script { superficial() }; sh "mvn -B test -Dtest='${GRUPO_A}' -Dsurefire.failIfNoSpecifiedTests=false" }
          post { always { deleteDir() } }
        }
        stage('Pruebas B') {
          agent { docker { image IMG } }
          steps { script { superficial() }; sh "mvn -B test -Dtest='${GRUPO_B}' -Dsurefire.failIfNoSpecifiedTests=false" }
          post { always { deleteDir() } }
        }
        stage('Empaquetar') {
          agent { docker { image IMG } }
          steps { script { superficial() }; sh 'mvn -B package -DskipTests' }
          post { always { deleteDir() } }
        }
      }
    }
  }
}
