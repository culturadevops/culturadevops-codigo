// El pipeline estándar del equipo. En el Jenkinsfile: pipelineEstandar(nombre: 'mi-proyecto')
def call(Map cfg = [:]) {
  pipeline {
    agent any
    stages {
      stage('Buscar secretos') {
        steps { sh '! grep -rnI --exclude-dir=.git "password=" .' }
      }
      stage('Compilar') {
        steps { sh './compilar.sh' }
      }
      stage('Pruebas') {
        steps { sh './probar.sh' }
      }
      stage('Empaquetar') {
        steps { empaquetar(cfg.nombre) }
      }
    }
    post {
      always { avisar(currentBuild.currentResult) }
    }
  }
}
