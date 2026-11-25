#!/bin/sh
# desplegar.sh IMAGEN:ETIQUETA — despliega SOLO si lo que hay ahora detrás de la etiqueta está firmado.
#
#   ./desplegar.sh tienda:3.0
#
# 1. cosign verifica la firma de la imagen a la que apunta la etiqueta, con la clave pública.
# 2. De su respuesta se saca el digest que se verificó.
# 3. Se arranca ESE digest, nunca la etiqueta: si alguien la mueve entre el paso 1 y el 3, da igual.
#
# cosign corre en un contenedor de la red interna «cadena-interna», que no tiene salida a internet:
# así es imposible que una firma o una verificación acabe en el registro público de transparencia.
set -eu

ref="${1:?uso: desplegar.sh IMAGEN:ETIQUETA}"
claves="${CLAVES:-$(pwd)/claves}"
cosign="ghcr.io/sigstore/cosign/cosign:v3.1.3"

if ! salida=$(docker run --rm --network cadena-interna -v "$claves:/claves:ro" "$cosign" \
        verify --key /claves/cosign.pub --allow-http-registry --insecure-ignore-tlog=true \
        "registro:5000/$ref" 2>&1); then
    echo "desplegar: NO. $ref no tiene una firma válida:"
    echo "$salida" | grep -i "error" | head -1 | sed 's/^/  /'
    exit 1
fi

digest=$(echo "$salida" | grep -o '"docker-manifest-digest":"sha256:[0-9a-f]*"' | head -1 | cut -d'"' -f4)
echo "desplegar: firma válida para $ref"
echo "desplegar: arranco el digest verificado, no la etiqueta: ${digest%"${digest#sha256:????????????}"}..."
docker run --rm "localhost:5000/${ref%%:*}@$digest"
