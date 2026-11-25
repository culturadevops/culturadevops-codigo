# Banco «Jenkins práctico» (cultura-devops 874-876). Jenkins LTS fijado + plugins fijados, sin asistente.
# plugins.txt: los 7 plugins pedidos (configuration-as-code job-dsl workflow-aggregator git docker-plugin
# credentials-binding matrix-auth) y todas sus dependencias, con la versión exacta que resolvió jenkins-plugin-cli
# el 2026-11-18. Con todo fijado, construir la imagen otro día da el mismo Jenkins.
FROM jenkins/jenkins:2.580.2-lts-jdk21
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc/jenkins.yaml
