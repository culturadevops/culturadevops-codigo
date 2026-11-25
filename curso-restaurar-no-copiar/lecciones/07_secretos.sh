#!/usr/bin/env bash
# Lección 7 · Los secretos: lo que convierte una restauración en un bloqueo.
#
# Haces bien las cosas: la copia va cifrada (age). La clave privada está en la máquina que hace
# las copias, que es lo cómodo. La máquina se muere. Tienes la copia, entera... y no la puedes abrir.
# Nadie lo descubre hasta el día que hace falta, porque cifrar no necesita la clave privada:
# solo la pública. Las copias se siguen haciendo «bien» todas las noches.
source /curso/comun.sh
set -o pipefail
sembrar 1000 >/dev/null
rm -f /root/.clave-copias /copias/*.age

titulo "7.1 · Una copia cifrada, como debe ser"
age-keygen -o /root/.clave-copias 2>&1 | sed 's/^/  /'
PUBLICA=$(age-keygen -y /root/.clave-copias)
pg_dump -Fc tienda | age -r "$PUBLICA" > /copias/tienda.dump.age
echo "  código de salida: $? · $(bytes /copias/tienda.dump.age) bytes · empieza por: $(head -c 21 /copias/tienda.dump.age)"
cp /root/.clave-copias /copias/clave-apartada.txt   # 7.3: una copia de la clave, FUERA de la máquina

titulo "7.2 · La máquina se muere. Restaurar con lo que queda"
rm -f /root/.clave-copias
echo "  ¿la copia está? $( [ -f /copias/tienda.dump.age ] && echo sí ) · ¿la clave? $( [ -f /root/.clave-copias ] && echo sí || echo NO )"
age -d -i /root/.clave-copias /copias/tienda.dump.age > /tmp/t.dump 2>/tmp/err; c=$?
echo "  age -d: código de salida $c · $(head -1 /tmp/err)"
# Y una nueva clave, por si acaso, no sirve de nada:
age-keygen -o /tmp/otra-clave 2>/dev/null
age -d -i /tmp/otra-clave /copias/tienda.dump.age > /tmp/t.dump 2>/tmp/err
echo "  con una clave nueva: $(head -1 /tmp/err)"

titulo "7.3 · Lo correcto: la clave apartada, y el ensayo la usa"
base_nueva restaurada
age -d -i /copias/clave-apartada.txt /copias/tienda.dump.age | pg_restore -d restaurada
echo "  código de salida: $? · pedidos restaurados: $(filas restaurada)"
echo "  ⚠️ «apartada» quiere decir otro sitio: un gestor de contraseñas, un sobre, otra cuenta."
echo "     Junto a las copias, como aquí por comodidad, cualquiera que robe las copias las abre."
