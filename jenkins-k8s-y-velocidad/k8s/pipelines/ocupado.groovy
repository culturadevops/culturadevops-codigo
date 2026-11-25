// 877 · El mismo pod de pod-agente.groovy, pero se queda 25 s trabajando para poder mirarlo desde kubectl.
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
    stage('Trabajo') {
      steps { container('maven') { sh 'echo POD=$(hostname); sleep 25' } }
    }
  }
}
