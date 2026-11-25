// Fija la URL de Jenkins al arrancar: sin ella, la CLI (que usa la demo) se niega a conectar.
import jenkins.model.JenkinsLocationConfiguration
def cfg = JenkinsLocationConfiguration.get()
cfg.setUrl("http://localhost:8080/")
cfg.save()
