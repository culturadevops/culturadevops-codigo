# Jenkins LTS con el plugin de git, sin el asistente de instalación (es una demo, sin usuarios).
FROM jenkins/jenkins:2.580.1-lts-jdk21
RUN jenkins-plugin-cli --plugins git credentials ssh-credentials plain-credentials >/dev/null
COPY url.groovy /usr/share/jenkins/ref/init.groovy.d/url.groovy
ENV JAVA_OPTS=-Djenkins.install.runSetupWizard=false
