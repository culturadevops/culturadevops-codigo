// avisar('SUCCESS') → una línea con el job, el build y el estado (aquí podría ir Slack o el correo)
def call(String estado) {
  echo "[aviso] ${env.JOB_NAME} #${env.BUILD_NUMBER}: ${estado}"
}
