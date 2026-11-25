# Jenkins del banco jenkins-k8s-y-velocidad (cultura-devops 877 y 878).
# LTS fijado + 73 plugins con versión fija (plugins.txt, sacado con jenkins-plugin-cli el 2026-11-18) + el cliente de Docker
# para los agentes `agent { docker }` del 878. Sin asistente: la configuración entra por JCasC (casc-*.yaml).
FROM docker:29.6.2-cli AS dockercli
FROM jenkins/jenkins:2.580.2-lts-jdk21
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli -f /usr/share/jenkins/ref/plugins.txt
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true"
ENV CASC_JENKINS_CONFIG=/casc/casc.yaml
