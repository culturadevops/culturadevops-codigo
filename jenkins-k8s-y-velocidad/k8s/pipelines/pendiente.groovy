// 877 · Un pod que pide más CPU de la que tiene el clúster (24 núcleos): ¿qué hace Jenkins?
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
      requests: {cpu: "32", memory: "512Mi"}
'''
    }
  }
  stages {
    stage('Compilar') {
      steps { container('maven') { sh 'mvn -v | head -1' } }
    }
  }
}
