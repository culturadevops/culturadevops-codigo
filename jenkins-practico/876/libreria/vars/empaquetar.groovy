// empaquetar('tienda-web') → tienda-web-<build>.tgz con lo que dejó la compilación
def call(String nombre) {
  def paquete = "${nombre}-${env.BUILD_NUMBER}.tgz"
  sh "tar czf ${paquete} build"
  echo "paquete: ${paquete}"
}
