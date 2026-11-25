// 878 · BASE: un agente Docker con la imagen oficial de Maven, tres etapas en fila y el checkout por defecto.
// Las dos pruebas que levantan MySQL y Postgres con Docker quedan fuera en TODAS las variantes: el agente ve el socket de
// Docker del controlador y Testcontainers las arrancaría en la máquina (31 s de espera y contenedores sueltos).
pipeline {
  agent { docker { image 'maven:3.9.11-eclipse-temurin-21' } }
  stages {
    stage('Compilar')   { steps { sh 'mvn -B compile' } }
    stage('Pruebas')    { steps { sh "mvn -B test -Dtest='!PostgresIntegrationTests,!MySqlIntegrationTests'" } }
    stage('Empaquetar') { steps { sh 'mvn -B package -DskipTests' } }
  }
  post {
    always { deleteDir() }
  }
}
