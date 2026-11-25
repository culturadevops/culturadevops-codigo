// Jobs del banco 874 (Job DSL, lo carga JCasC). Los mismos dos pipelines en el agente fijo y en el efímero.
def estado = '''pipeline {
  agent { label 'ETIQUETA' }
  stages {
    stage('Build') {
      steps {
        sh \'\'\'#!/bin/sh
          echo "agente: $NODE_NAME · contenedor: $(hostname)"
          echo "archivos que ya había en el workspace: $(ls | wc -l)  $(ls | tr '\\\\n' ' ')"
          echo "build $BUILD_NUMBER" > salida-$BUILD_NUMBER.txt
          if [ "$INSTALAR" = "true" ]; then
            mkdir -p ~/bin
            printf '#!/bin/sh\\\\necho "mi-linter 1.0: 0 problemas"\\\\n' > ~/bin/mi-linter
            chmod +x ~/bin/mi-linter
            echo "instalé mi-linter en ~/bin"
          fi
          ~/bin/mi-linter
        \'\'\'
      }
    }
  }
}
'''

def vacio = '''pipeline {
  agent { label 'ETIQUETA' }
  stages { stage('Uno') { steps { sh 'date +%s%3N' } } }
}
'''

['fijo', 'efimero'].each { lbl ->
  pipelineJob('estado-' + lbl) {
    parameters { booleanParam('INSTALAR', true, 'instalar mi-linter antes de usarlo') }
    definition { cps { sandbox(true); script(estado.replace('ETIQUETA', lbl)) } }
  }
  pipelineJob('vacio-' + lbl) {
    definition { cps { sandbox(true); script(vacio.replace('ETIQUETA', lbl)) } }
  }
}
