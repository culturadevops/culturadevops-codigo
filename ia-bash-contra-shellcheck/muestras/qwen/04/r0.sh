#!/bin/bash

# Verificar si se proporcionó un argumento
if [ -z "$1" ]; then
    echo "Uso: $0 DIR"
    exit 1
fi

# Asignar el argumento a DIR
DIR=$1

# Verificar si DIR existe
if [ ! -d "$DIR" ]; then
    echo "El directorio $DIR no existe."
    exit 1
fi

# Encontrar y eliminar archivos y directorios con más de 30 días de inactividad
find "$DIR" -type f -mtime +30 -exec rm -f {} \;
find "$DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "Archivos y directorios con más de 30 días de inactividad han sido eliminados."
