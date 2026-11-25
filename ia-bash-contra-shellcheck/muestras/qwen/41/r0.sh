#!/bin/bash

# Comprobar si las variables de entorno necesarias existen y no están vacías
if [ -z "${DB_HOST}" ] || [ -z "${DB_USER}" ] || [ -z "${DB_PASS}" ]; then
    echo "Faltan variables de entorno:"
    if [ -z "${DB_HOST}" ]; then echo "DB_HOST"; fi
    if [ -z "${DB_USER}" ]; then echo "DB_USER"; fi
    if [ -z "${DB_PASS}" ]; then echo "DB_PASS"; fi
    exit 1
fi

echo " Todas las variables de entorno necesarias están definidas y no están vacías."
exit 0
