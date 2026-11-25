// 877 · Un contenedor con límite de 128 MiB que intenta reservar 300 MiB.
pipeline {
  agent {
    kubernetes {
      yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: node
    image: node:22.21.1-alpine
    command: ["sleep"]
    args: ["infinity"]
    resources:
      requests: {cpu: "250m", memory: "128Mi"}
      limits: {memory: "128Mi"}
'''
    }
  }
  stages {
    stage('Pruebas') {
      steps {
        container('node') {
          sh 'node -e "const b = Buffer.alloc(300 * 1024 * 1024, 1); console.log(\'reservados\', b.length)"'
        }
      }
    }
  }
}
