#!/bin/bash

# Verificar si se proporcionaron dos argumentos
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 DIR DEST"
    exit 1
fi

DIR=$1
DEST=$2

# Verificar si el directorio de origen existe
if [ ! -d "$DIR" ]; then
    echo "El directorio de origen no existe."
    exit 1
fi

# Verificar si el directorio de destino existe, si no, crearlo
if [ ! -d "$DEST" ]; then
    mkdir -p "$DEST"
fi

# Obtener la fecha actual en formato AAAAMMDD
DATE=$(date +%Y%m%d)

# Crear el archivo de respaldo comprimido
tar -czf "$DEST/respaldo-$DATE.tar.gz" -C "$DIR" .

echo "Respaldo creado: $DEST/respaldo-$DATE.tar.gz"
