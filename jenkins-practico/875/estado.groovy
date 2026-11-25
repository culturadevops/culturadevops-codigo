// Huella del estado de Jenkins (banco 875): lo que JCasC debe dejar igual en un contenedor nuevo.
import jenkins.model.Jenkins
import java.security.MessageDigest

def j = Jenkins.get()
def md5 = { String s -> MessageDigest.getInstance('MD5').digest(s.getBytes('UTF-8')).encodeHex().toString().substring(0, 12) }
println 'mensaje:      ' + j.systemMessage
println 'ejecutores:   ' + j.numExecutors + ' en el controlador'
println 'usuarios:     ' + hudson.model.User.getAll().collect { it.id }.sort().join(', ')
println 'seguridad:    ' + j.securityRealm.getClass().simpleName + ' + ' + j.authorizationStrategy.getClass().simpleName
def creds = com.cloudbees.plugins.credentials.SystemCredentialsProvider.getInstance().getCredentials()
println 'credenciales: ' + creds.collect { it.id + ' (' + it.getClass().simpleName + ')' }.sort().join(', ')
println 'nubes:        ' + j.clouds.collect { c -> c.name + ': ' + c.templates.collect { t -> t.labelString + ' = ' + t.image }.join(', ') }.join('; ')
j.getAllItems(hudson.model.Job).sort { it.fullName }.each { job ->
  println 'job:          ' + job.fullName + ' · config.xml md5 ' + md5(job.configFile.file.text) + ' · último build: ' + (job.lastBuild?.number ?: 'ninguno')
}
