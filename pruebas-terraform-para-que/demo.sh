#!/usr/bin/env bash
# demo.sh — la medición del vídeo 222 «Para qué sirve Terraform y para qué NO».
#
# ⛔ LA TRAMPA QUE ESTE GUION EVITA A PROPÓSITO. La comparación fácil es «a mano hay que
# cambiar el nombre en quince sitios y con código es una variable». Es MENTIRA: un guion de
# shell con una variable también escala, y el a_mano.sh de al lado lo demuestra. Si montas
# ahí tu argumento, cualquiera que sepa shell te lo tumba en los comentarios.
#
# Lo que de verdad separa a las dos formas no es parametrizar. Es que una LLEVA LA CUENTA de
# lo que creó y la otra no. Así que se mide eso, que es lo honesto:
#
#   1. levantar          (a mano gana, y se dice claramente)
#   2. volver a ejecutarlo con el entorno ya puesto   <- aquí revienta el guion
#   3. contestar «¿qué hay levantado?»
#   4. alguien toca por fuera: ¿se entera alguien?
#   5. destruir sin dejar basura
set -u
D=$(cd "$(dirname "$0")" && pwd -W)

tofu() {
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$D/tofu:/w" -w /w ghcr.io/opentofu/opentofu:latest "$@"
}

limpiar() {
  docker rm -f pruebas-db pruebas-cache pruebas-app-1 pruebas-app-2 >/dev/null 2>&1
  docker network rm pruebas-red >/dev/null 2>&1
  docker volume rm pruebas-datos >/dev/null 2>&1
}
limpiar
rm -f "$D/tofu/terraform.tfstate" "$D/tofu/terraform.tfstate.backup" 2>/dev/null

echo "== 1 · LEVANTAR EL ENTORNO =="
echo "   (una red, un volumen, una base de datos, una cache y dos copias de la app)"
t0=$(date +%s%N); sh "$D/a_mano.sh"; t1=$(date +%s%N)
MANO=$(( (t1 - t0) / 1000000 ))
echo "   a mano:      ${MANO} ms"
limpiar
t0=$(date +%s%N); tofu apply -auto-approve -no-color >/dev/null 2>&1; t1=$(date +%s%N)
CODIGO=$(( (t1 - t0) / 1000000 ))
echo "   con codigo:  ${CODIGO} ms"
echo
echo "   >>> GANA A MANO, y se dice tal cual en el video. Para levantar UNA vez, escribir"
echo "       codigo es mas lento y mas trabajo. Quien te venda lo contrario te esta vendiendo algo."

echo
echo "== 2 · Y AHORA LO EJECUTAS OTRA VEZ, con el entorno ya puesto =="
echo "   a mano:"
sh "$D/a_mano.sh" 2>&1 | head -2 | sed 's/^/     /'
echo "     ^ y aqui es donde se acaba el guion de shell: no sabe que ya existe."
echo -n "     (y ademas se quedo a medias: piezas creadas antes de reventar) "
docker ps -a --filter "name=pruebas-" --format '{{.Names}}' | wc -l
echo "   con codigo:"
tofu apply -auto-approve -no-color 2>&1 | grep -E 'No changes|Apply complete' | sed 's/^/     /'

echo
echo "== 3 · ¿QUE HAY LEVANTADO? =="
echo "   a mano: la respuesta honesta es mirar docker ps y adivinar que es de quien."
echo "   con codigo, la lista es exacta:"
tofu state list -no-color 2>/dev/null | sed 's/^/     /'
echo -n "   piezas de las que lleva la cuenta: "
tofu state list -no-color 2>/dev/null | wc -l

echo
echo "== 4 · ALGUIEN TOCA POR FUERA (el martes, con prisa) =="
docker rm -f pruebas-app-2 >/dev/null
echo "   borro un contenedor a mano y le pregunto al codigo que ve:"
tofu plan -no-color 2>&1 | grep -E 'Plan:|will be created' | sed 's/^/     /' | head -3
echo "   y lo repone solo:"
tofu apply -auto-approve -no-color >/dev/null 2>&1
echo -n "     contenedores vivos tras el apply: "
docker ps --filter "name=pruebas-" --format '{{.Names}}' | wc -l
echo "   ^ el guion de shell no se habria enterado NUNCA de que faltaba uno."

echo
echo "== 5 · DESTRUIR SIN DEJAR BASURA =="
echo -n "   a mano: a_mano.sh no tiene destruccion. Lineas de borrado en el fichero: "
grep -cE 'docker (rm|network rm|volume rm)' "$D/a_mano.sh" || true
echo "   (hay que escribir un segundo guion, y mantenerlo en sintonia con el primero)"
t0=$(date +%s%N); tofu destroy -auto-approve -no-color >/dev/null 2>&1; t1=$(date +%s%N)
echo "   con codigo: destruido en $(( (t1 - t0) / 1000000 )) ms, sin escribir nada"
echo -n "     contenedores 'pruebas-' que quedan: "
docker ps -a --filter "name=pruebas-" --format '{{.Names}}' | wc -l
echo -n "     redes 'pruebas-' que quedan:        "
docker network ls --filter "name=pruebas-" --format '{{.Name}}' | wc -l
echo -n "     volumenes 'pruebas-' que quedan:    "
docker volume ls --filter "name=pruebas-" --format '{{.Name}}' | wc -l
echo "   ^ el volumen es el que siempre se queda olvidado cuando se destruye a mano,"
echo "     y es justo el que cuesta dinero todos los meses."

limpiar
echo
echo "== limpio =="
