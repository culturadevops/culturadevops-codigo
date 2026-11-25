// 877 · Un build = un pod con tres contenedores: jnlp (el agente), maven y node.
pipeline {
  agent {
    kubernetes {
      yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: maven
    image: maven:3.9.11-eclipse-temurin-21
    command: ["sleep"]
    args: ["infinity"]
    resources:
      requests: {cpu: "500m", memory: "512Mi"}
      limits: {memory: "1Gi"}
  - name: node
    image: node:22.21.1-alpine
    command: ["sleep"]
    args: ["infinity"]
    resources:
      requests: {cpu: "250m", memory: "256Mi"}
      limits: {memory: "512Mi"}
'''
    }
  }
  stages {
    stage('Agente listo') {
      steps {
        sh 'echo "T_AGENTE=$(date +%s%3N) INICIO=' + currentBuild.startTimeInMillis + ' POD=$(hostname)"'
      }
    }
    stage('Backend') {
      steps { container('maven') { sh 'mvn -v | head -1; java -version 2>&1 | head -1' } }
    }
    stage('Frontend') {
      steps { container('node') { sh 'node -v; npm -v' } }
    }
  }
}
