#!/bin/bash

# Verificar si se proporcionaron tres argumentos
if [ "$#" -ne 3 ]; then
    echo "Uso: $0 DIR VIEJO NUEVO"
    exit 1
fi

DIR="$1"
VIEJO="$2"
NUEVO="$3"

# Verificar si DIR existe
if [ ! -d "$DIR" ]; then
    echo "El directorio $DIR no existe."
    exit 1
fi

# Recorrer todos los archivos .conf en el directorio y sus subdirectorios
find "$DIR" -type f -name "*.conf" | while read -r archivo; do
    # Crear una copia del archivo original
    cp "$archivo" "${archivo}.orig"
    
    # Reemplazar el texto VIEJO por NUEVO en el archivo
    sed -i "s/$VIEJO/$NUEVO/g" "$archivo"
done

echo "Reemplazo completado."
