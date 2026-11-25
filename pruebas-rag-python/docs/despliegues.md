# Despliegues a producción

Se despliega a producción de lunes a jueves, entre las 10:00 y las 16:00. Los viernes no se despliega salvo un arreglo urgente aprobado por la guardia.

Todo despliegue pasa primero por el entorno de staging y necesita las pruebas en verde y la aprobación de otra persona del equipo en la solicitud de cambio.

Para revertir un despliegue se usa el comando deploy rollback con el número de versión anterior. Revertir no necesita aprobación: primero se revierte y después se investiga.

Durante la semana de cierre de mes, del día 28 al día 2, hay congelamiento: solo se despliegan arreglos de seguridad.
