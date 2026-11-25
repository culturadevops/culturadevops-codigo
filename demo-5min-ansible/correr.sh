#!/bin/bash
# Corre DENTRO de python:3.13-slim (lo lanza ejecutar.sh). Salida literal → SALIDA.md.
set -u
pip install -q ansible-core==2.21.5 >/dev/null 2>&1
rm -rf /w && mkdir -p /w && cp /trabajo/inventario.ini /trabajo/playbook.yml /trabajo/playbook-mal.yml /w/ && cd /w
export ANSIBLE_NOCOLOR=1 ANSIBLE_LOCALHOST_WARNING=0 ANSIBLE_INVENTORY_UNPARSED_WARNING=0
echo "\$ ansible --version"
ansible --version | head -1
echo
echo "### La primera versión (dos tareas tocan el mismo archivo)"
echo "\$ ansible-playbook -i inventario.ini playbook-mal.yml   # 1ª vez"
ansible-playbook -i inventario.ini playbook-mal.yml 2>&1 | grep -E "web[12] *:"
echo "\$ ansible-playbook -i inventario.ini playbook-mal.yml   # 2ª vez, sin cambiar nada"
ansible-playbook -i inventario.ini playbook-mal.yml 2>&1 | grep -E "web[12] *:"
rm -rf /srv/web1 /srv/web2
echo
echo "### La versión buena (una sola tarea escribe el archivo)"
echo "\$ ansible-playbook -i inventario.ini playbook.yml   # 1ª vez"
ansible-playbook -i inventario.ini playbook.yml 2>&1 | grep -E "web[12] *:"
echo "\$ cat /srv/web1/app/app.conf"
cat /srv/web1/app/app.conf
echo "\$ ansible-playbook -i inventario.ini playbook.yml   # 2ª vez, sin cambiar nada"
ansible-playbook -i inventario.ini playbook.yml 2>&1 | grep -E "web[12] *:"
echo
echo "\$ ansible-playbook -i inventario.ini playbook.yml -e puerto=9090 --check --diff   # ¿qué cambiaría?"
ansible-playbook -i inventario.ini playbook.yml -e puerto=9090 --check --diff 2>&1 | grep -E "^[-+]puerto|web[12] *:"
