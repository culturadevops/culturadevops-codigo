# SALIDA — Ansible en 5 minutos (cultura-devops)

> Corrida del 2026-10-19 17:14 en python:3.13-slim con ansible-core 2.21.5. Los dos «servidores» son el mismo contenedor (conexión local).

```
$ ansible --version
ansible [core 2.21.5]

### La primera versión (dos tareas tocan el mismo archivo)
$ ansible-playbook -i inventario.ini playbook-mal.yml   # 1ª vez
web1                       : ok=4    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
web2                       : ok=4    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
$ ansible-playbook -i inventario.ini playbook-mal.yml   # 2ª vez, sin cambiar nada
web1                       : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
web2                       : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

### La versión buena (una sola tarea escribe el archivo)
$ ansible-playbook -i inventario.ini playbook.yml   # 1ª vez
web1                       : ok=3    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
web2                       : ok=3    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
$ cat /srv/web1/app/app.conf
servidor = web1
puerto = 8080
mantenimiento = no
$ ansible-playbook -i inventario.ini playbook.yml   # 2ª vez, sin cambiar nada
web1                       : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
web2                       : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

$ ansible-playbook -i inventario.ini playbook.yml -e puerto=9090 --check --diff   # ¿qué cambiaría?
-puerto = 8080
+puerto = 9090
-puerto = 8080
+puerto = 9090
web1                       : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
web2                       : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```
