#!/bin/bash

DIR=$1
DEST=$2

# Verifica si los directorios existen
if [ ! -d "$DIR" ]; then
    echo "El directorio $DIR no existe."
    exit 1
fi

if [ ! -d "$DEST" ]; then
    echo "El directorio $DEST no existe."
    exit 1
fi

# Crea el nombre del archivo de respaldo con la fecha y hora
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$DEST/backup_$DIR_$TIMESTAMP.tar.gz"

# Realiza el respaldo
tar -czf "$BACKUP_FILE" -C "$DIR" .

# Lista todos los archivos .tar.gz en DEST
tar_files=$(find "$DEST" -maxdepth 1 -type f -name "*.tar.gz")

# Mantiene solo los 3 archivos más recientes
echo "$tar_files" | sort -r | sed -n '4,$p' | xargs -d '\n' rm -f

echo "Respaldo creado: $BACKUP_FILE"
