# Respaldos de las bases de datos

La base de datos de clientes se respalda cada noche a las 02:00 con pg_dump y el archivo se sube a un bucket con versionado activado.

Los respaldos diarios se guardan 35 días. El respaldo del primer día de cada mes se guarda un año.

Una vez al mes se restaura el último respaldo en una base de datos vacía y se cuentan las filas de las tablas principales. Un respaldo que nunca se restauró no cuenta como respaldo.

Si el respaldo de la noche falla, la alerta llega a la guardia con severidad alta.
