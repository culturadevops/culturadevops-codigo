#!/usr/bin/env bash
# Repo del banco: spring-petclinic fijado en 500158f7 (2026-09-29) + un commit con los Jenkinsfile del banco, rama «banco».
# Jenkins lo lee por file:// (montado en /repos). petclinic-origen.git = git clone --bare de spring-projects/spring-petclinic.
set -euo pipefail
cd "$(dirname "$0")"
FIJO=500158f732419217507c7656904b8e6aa1bcc0d6
rm -rf petclinic.git _trabajo petclinic-src && git clone -q --bare petclinic-origen.git petclinic.git
git clone -q petclinic.git _trabajo && cd _trabajo
git checkout -q -b banco $FIJO
mkdir -p jenkins && cp ../jenkinsfiles/*.Jenkinsfile jenkins/
git add jenkins && git -c user.name=banco -c user.email=banco@localhost commit -q -m "Jenkinsfiles del banco 878"
git push -q origin banco
cd .. && rm -rf _trabajo
git --git-dir=petclinic.git log --oneline banco | wc -l | xargs echo "commits en la rama banco:"
# Copia de las fuentes (sin .git, con LF) para calentar la imagen de agente preparada (Dockerfile.agente).
git -c core.autocrlf=false clone -q petclinic.git -b banco petclinic-src && rm -rf petclinic-src/.git petclinic-src/jenkins
