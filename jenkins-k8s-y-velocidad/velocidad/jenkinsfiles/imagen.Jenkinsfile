// 878 · IMAGEN PREPARADA: lo mismo que la base, con una imagen de agente que ya trae las dependencias dentro.
pipeline {
  agent { docker { image 'jk-b-agente-petclinic:1' } }
  stages {
    stage('Compilar')   { steps { sh 'mvn -B compile' } }
    stage('Pruebas')    { steps { sh "mvn -B test -Dtest='!PostgresIntegrationTests,!MySqlIntegrationTests'" } }
    stage('Empaquetar') { steps { sh 'mvn -B package -DskipTests' } }
  }
  post {
    always { deleteDir() }
  }
}
