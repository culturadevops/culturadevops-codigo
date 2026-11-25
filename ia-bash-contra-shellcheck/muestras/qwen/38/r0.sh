#!/bin/bash

NOMBRE=$1
LOGFILE=$2
COMANDO=$3

if ! pgrep -x "$NOMBRE" > /dev/null
then
    $COMANDO &>> "$LOGFILE" &
    echo "reiniciado" >> "$LOGFILE"
fi
