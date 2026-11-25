# -*- coding: utf-8 -*-
"""Las 50 tareas fijas del vídeo 704 (cultura-devops). Fijadas el 2026-10-29 ANTES de generar ningún script.

Cada tarea:
  tarea  -> lo que se le pide a la IA (va literal en el prompt)
  uso    -> la interfaz que tiene que respetar (va literal en el prompt)
  run    -> cómo la llama el banco (bash; $1 = ruta del script; $D, $DEST, $S vienen del accesorio)
  check  -> bash que devuelve 0 si la tarea quedó hecha ($OUT = stdout, $ERR = stderr, $RC = código de salida)
  pre    -> (opcional) bash que se ejecuta antes
El accesorio (fixture) está en runner.sh. $S es "_" en la pasada de control y " " en la pasada con espacios.

Criterio fijado antes de mirar resultados:
  - «funciona»        = el check pasa en la pasada de control (nombres sin espacios)
  - «rompe con espacios» = pasa en control y falla con espacios
  - «limpio»          = shellcheck 0.11.0 sin ningún aviso, de ningún nivel
  - «trampa»          = cada `shellcheck disable` nuevo frente a la ronda 0
Muestra de Claude Code: las 20 tareas impares del 1 al 39 (fijada antes de generar).
"""

T = [
    dict(id=1, tarea="Copia todos los archivos .log de DIR (sin entrar en subcarpetas) a DEST, creando DEST si no existe.",
         uso="script.sh DIR DEST", run='bash "$1" "$D" "$DEST"',
         check='[ -f "$DEST/app.log" ] && [ -f "$DEST/error${S}del${S}servidor.log" ] && [ -f "$DEST/registro${S}antiguo.log" ]'),
    dict(id=2, tarea="Crea un respaldo comprimido de DIR dentro de DEST, con el nombre respaldo-AAAAMMDD.tar.gz (fecha de hoy).",
         uso="script.sh DIR DEST", run='bash "$1" "$D" "$DEST"',
         check='f=$(find "$DEST" -name "respaldo-*.tar.gz" -mmin -10 | head -1); [ -n "$f" ] && tar -tzf "$f" | grep -q "informe${S}final.txt"'),
    dict(id=3, tarea="Rota el archivo de log FILE: si existe, lo renombra a FILE.1 (el FILE.1 anterior pasa a FILE.2, y así hasta FILE.5; "
                     "el más viejo se borra) y crea un FILE nuevo vacío.",
         uso="script.sh FILE", run='bash "$1" "$D/error${S}del${S}servidor.log"',
         check='F="$D/error${S}del${S}servidor.log"; [ -s "$F.1" ] && [ -f "$F" ] && [ ! -s "$F" ]'),
    dict(id=4, tarea="Borra los archivos de DIR (incluidas las subcarpetas) con más de 30 días desde su última modificación.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ ! -e "$D/copia${S}vieja.bak" ] && [ ! -e "$D/registro${S}antiguo.log" ] && [ -f "$D/app.log" ] && [ -f "$D/informe${S}final.txt" ]'),
    dict(id=5, tarea="Imprime cada archivo .txt de DIR (sin subcarpetas) con su número de líneas, en el formato 'NOMBRE: N', una por línea, "
                     "donde NOMBRE es el nombre del archivo sin la ruta.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='grep -qE "informe${S}final\\.txt: ?3$" "$OUT"'),
    dict(id=6, tarea="Cuenta las líneas que contienen la palabra ERROR en todos los archivos .log de DIR, incluidas las subcarpetas, "
                     "e imprime solo el número total.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ "$(tr -d "[:space:]" < "$OUT")" = 7 ]'),
    dict(id=7, tarea="Comprime con gzip cada archivo .log de DIR (sin subcarpetas) que no esté comprimido.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ -f "$D/error${S}del${S}servidor.log.gz" ] && [ -f "$D/app.log.gz" ]'),
    dict(id=8, tarea="Cambia a minúsculas la extensión de todos los archivos de DIR (por ejemplo, FOTO.JPG pasa a FOTO.jpg; "
                     "el resto del nombre no cambia).",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ -f "$D/foto${S}de${S}perfil.jpg" ] && [ ! -e "$D/foto${S}de${S}perfil.JPG" ]'),
    dict(id=9, tarea="Genera dentro de DIR un archivo SHA256SUMS con la suma sha256 de cada archivo regular de DIR (sin subcarpetas), "
                     "en el formato de sha256sum.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='(cd "$D" && sha256sum -c SHA256SUMS 2>/dev/null | grep -q "informe${S}final.txt: OK")'),
    dict(id=10, tarea="Imprime el tamaño total de DIR en kilobytes (solo el número) y, si pasa de LIMITE kilobytes, termina con código 2.",
         uso="script.sh DIR LIMITE", run='bash "$1" "$D" 1',
         check='[ "$RC" -eq 2 ] && grep -qE "^[0-9]+" "$OUT"'),
    dict(id=11, tarea="Organiza DIR: mueve cada archivo regular de DIR (sin subcarpetas) a una subcarpeta de DIR con el nombre de su "
                      "extensión en minúsculas (txt/, log/, etc.).",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ -f "$D/txt/informe${S}final.txt" ] && [ -f "$D/log/error${S}del${S}servidor.log" ]'),
    dict(id=12, tarea="Lista los 3 archivos más grandes de DIR (incluidas las subcarpetas), uno por línea con su ruta, "
                      "del más grande al más pequeño.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='head -1 "$OUT" | grep -q "registro${S}antiguo.log"'),
    dict(id=13, tarea="Lee el archivo CSV FILE (la primera línea es la cabecera: nombre,correo) e imprime solo los correos, uno por línea.",
         uso="script.sh FILE", run='bash "$1" "$D/sub${S}carpeta/usuarios.csv"',
         check='grep -qx "ana@ejemplo.com" "$OUT" && grep -qx "luis@ejemplo.com" "$OUT" && ! grep -q correo "$OUT"'),
    dict(id=14, tarea="Lee FILE, que tiene un nombre de servicio por línea, y para cada uno comprueba con pgrep si hay un proceso con ese "
                      "nombre; imprime 'NOMBRE: activo' o 'NOMBRE: caído'. Termina con código 1 si alguno está caído.",
         uso="script.sh FILE", run='bash "$1" "$D/servicios${S}a${S}vigilar.txt"',
         pre='sleep 300 >/dev/null 2>&1 &',
         check='grep -q "sleep: activo" "$OUT" && grep -qE "noexiste-xyz: ca(í|i)do" "$OUT" && [ "$RC" -eq 1 ]'),
    dict(id=15, tarea="Añade al principio del nombre de cada archivo .txt de DIR (sin subcarpetas) su fecha de modificación en formato "
                      "AAAA-MM-DD_ (ejemplo: notas.txt pasa a 2026-10-29_notas.txt).",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='find "$D" -maxdepth 1 -name "????-??-??_informe${S}final.txt" | grep -q .'),
    dict(id=16, tarea="Borra todos los archivos que terminan en .tmp o .bak dentro de DIR y sus subcarpetas, e imprime cuántos borró.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ ! -e "$D/copia${S}vieja.bak" ] && [ ! -e "$D/sub${S}carpeta/temp${S}de${S}trabajo.tmp" ] && [ -f "$D/app.log" ] && grep -q 2 "$OUT"'),
    dict(id=17, tarea="Copia a DEST los archivos de DIR (incluidas las subcarpetas, conservando la estructura) que no existan en DEST "
                      "o que sean más nuevos que su copia. No uses rsync.",
         uso="script.sh DIR DEST", run='bash "$1" "$D" "$DEST"',
         check='[ -f "$DEST/sub${S}carpeta/otro${S}archivo.log" ] && [ -f "$DEST/app.log" ]'),
    dict(id=18, tarea="Vacía (deja en 0 bytes, sin borrarlos) los archivos .log de DIR que pesen más de 100 KB.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ -f "$D/registro${S}antiguo.log" ] && [ ! -s "$D/registro${S}antiguo.log" ] && [ -s "$D/app.log" ]'),
    dict(id=19, tarea="Busca archivos duplicados (con el mismo contenido) dentro de DIR y sus subcarpetas, e imprime cada grupo de rutas "
                      "duplicadas.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='grep -q "copia${S}del${S}informe.txt" "$OUT" && grep -q "informe${S}final.txt" "$OUT"'),
    dict(id=20, tarea="Da permiso de ejecución a todos los archivos .sh de DIR y sus subcarpetas, y quita el permiso de escritura "
                      "para otros usuarios a todos los archivos de DIR.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ -x "$D/sub${S}carpeta/mi${S}script.sh" ]'),
    dict(id=21, tarea="Ejecuta el comando que recibe después de LOGFILE (con sus argumentos) y añade su salida a LOGFILE, con cada línea "
                      "precedida de la fecha y hora en formato [AAAA-MM-DD HH:MM:SS].",
         uso="script.sh LOGFILE COMANDO [ARGUMENTOS...]", run='bash "$1" "$D/salida${S}del${S}comando.log" ls "$D"',
         check='grep -qE "^\\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\\] ?informe" "$D/salida${S}del${S}comando.log"'),
    dict(id=22, tarea="Ejecuta el comando recibido como argumentos hasta 3 veces, esperando 1 segundo entre intentos, y termina con el "
                      "código de salida del último intento.",
         uso="script.sh COMANDO [ARGUMENTOS...]", run='bash "$1" test -f "$D/informe${S}final.txt"',
         check='[ "$RC" -eq 0 ]'),
    dict(id=23, tarea="Evita que dos copias del script se ejecuten a la vez usando flock sobre el archivo de bloqueo LOCKFILE; "
                      "con el bloqueo tomado, escribe la línea 'trabajando' en LOGFILE.",
         uso="script.sh LOCKFILE LOGFILE", run='bash "$1" "$D/mi${S}tarea.lock" "$D/registro${S}de${S}tarea.txt"',
         check='grep -q trabajando "$D/registro${S}de${S}tarea.txt"'),
    dict(id=24, tarea="Extrae de FILE (un log de acceso de nginx en formato combinado) las 5 IP con más peticiones e imprímelas en el "
                      "formato 'N IP', de mayor a menor.",
         uso="script.sh FILE", run='bash "$1" "$D/acceso${S}del${S}sitio.log"',
         check='head -1 "$OUT" | grep -q "10\\.0\\.0\\.1$"'),
    dict(id=25, tarea="Lee el archivo de configuración FILE (líneas CLAVE=valor; las que empiezan con # son comentarios) e imprime el "
                      "valor de la clave CLAVE.",
         uso="script.sh FILE CLAVE", run='bash "$1" "$D/config.conf" ruta_datos',
         check='grep -qx "/srv/datos${S}de${S}app" "$OUT"'),
    dict(id=26, tarea="Lista los usuarios del sistema (de /etc/passwd) cuya shell es /bin/bash, uno por línea.",
         uso="script.sh", run='bash "$1"',
         check='grep -qx root "$OUT"'),
    dict(id=27, tarea="Lee FILE, que tiene una ruta por línea, e imprime 'FALTA: RUTA' por cada ruta que no exista. "
                      "Termina con código 1 si falta alguna.",
         uso="script.sh FILE", run='bash "$1" "$D/rutas.txt"',
         check='grep -q "FALTA: .*no${S}existe.txt" "$OUT" && ! grep -q "FALTA: .*informe" "$OUT" && [ "$RC" -eq 1 ]'),
    dict(id=28, tarea="Reemplaza el texto VIEJO por NUEVO en todos los archivos .conf de DIR y sus subcarpetas, guardando antes una "
                      "copia .orig de cada archivo modificado.",
         uso="script.sh DIR VIEJO NUEVO", run='bash "$1" "$D" "puerto=8080" "puerto=9090"',
         check='grep -q "puerto=9090" "$D/config.conf" && [ -f "$D/config.conf.orig" ]'),
    dict(id=29, tarea="Imprime los archivos de DIR (incluidas las subcarpetas) modificados en las últimas 24 horas, uno por línea.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='grep -q "informe${S}final.txt" "$OUT" && ! grep -q "copia${S}vieja" "$OUT"'),
    dict(id=30, tarea="Crea en DEST un respaldo tar.gz de DIR con la fecha y la hora en el nombre, y luego deja en DEST solo los 3 "
                      "respaldos .tar.gz más recientes.",
         uso="script.sh DIR DEST", run='bash "$1" "$D" "$DEST"',
         check='n=$(find "$DEST" -name "*.tar.gz" | wc -l); f=$(find "$DEST" -name "*.tar.gz" -mmin -10 | head -1); '
               '[ "$n" -le 3 ] && [ -n "$f" ] && tar -tzf "$f" | grep -q "informe${S}final.txt"'),
    dict(id=31, tarea="Imprime el tamaño de cada subcarpeta directa de DIR en formato legible (como du -h), de la más grande a la más pequeña.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='grep -q "sub${S}carpeta" "$OUT"'),
    dict(id=32, tarea="Convierte los finales de línea de Windows (CRLF) a Unix (LF) en todos los archivos .txt de DIR, sin usar dos2unix.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='! grep -q "$(printf "\\r")" "$D/notas${S}de${S}junio.txt" && [ "$(wc -l < "$D/notas${S}de${S}junio.txt")" -eq 2 ]'),
    dict(id=33, tarea="Junta en un solo archivo DEST/todo.log el contenido de todos los .log de DIR (incluidas las subcarpetas), "
                      "ordenados por nombre de archivo.",
         uso="script.sh DIR DEST", run='bash "$1" "$D" "$DEST"',
         check='grep -q "linea del otro archivo" "$DEST/todo.log" && grep -q "linea de app" "$DEST/todo.log"'),
    dict(id=34, tarea="Revisa con df el porcentaje de uso del sistema de archivos donde está DIR e imprime 'ALERTA' si pasa de UMBRAL "
                      "por ciento, u 'OK' si no.",
         uso="script.sh DIR UMBRAL", run='bash "$1" "$D" 0',
         check='grep -q ALERTA "$OUT"'),
    dict(id=35, tarea="Lee FILE (un nombre de usuario por línea) e imprime el comando useradd que ejecutaría para cada uno, sin "
                      "ejecutarlo (modo de prueba).",
         uso="script.sh FILE", run='bash "$1" "$D/nuevos${S}usuarios.txt"',
         check='grep -q "useradd.*ana" "$OUT" && grep -q "useradd.*luis" "$OUT"'),
    dict(id=36, tarea="Descomprime cada archivo .tar.gz de DIR en una carpeta de DIR con el mismo nombre sin la extensión.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='find "$D/paquete${S}de${S}prueba" -name dentro.txt 2>/dev/null | grep -q .'),
    dict(id=37, tarea="Cuenta cuántos archivos hay de cada extensión en DIR (incluidas las subcarpetas) e imprime 'EXT N' por línea, "
                      "de mayor a menor.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='grep -qE "^\\.?log:? +[0-9]+$" "$OUT"'),
    dict(id=38, tarea="Comprueba si hay un proceso llamado NOMBRE; si no lo hay, ejecuta el COMANDO dado (con sus argumentos) en segundo "
                      "plano y escribe la línea 'reiniciado' en LOGFILE.",
         uso="script.sh NOMBRE LOGFILE COMANDO [ARGUMENTOS...]", run='bash "$1" noexiste-xyz "$D/registro${S}reinicios.log" sleep 1',
         check='grep -q reiniciado "$D/registro${S}reinicios.log"'),
    dict(id=39, tarea="Mueve cada archivo .log de DIR (sin subcarpetas) a una subcarpeta de DIR llamada AAAA-MM según su fecha de "
                      "modificación.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='find "$D" -mindepth 2 -path "*/20[0-9][0-9]-[0-9][0-9]/*" -name "error${S}del${S}servidor.log" | grep -q .'),
    dict(id=40, tarea="Elimina los espacios en blanco al final de cada línea en todos los archivos .txt de DIR (sin subcarpetas).",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='! grep -q " $" "$D/informe${S}final.txt" && [ "$(wc -l < "$D/informe${S}final.txt")" -eq 3 ]'),
    dict(id=41, tarea="Comprueba que las variables de entorno DB_HOST, DB_USER y DB_PASS existen y no están vacías; imprime cuáles faltan "
                      "y termina con código 1 si falta alguna.",
         uso="DB_HOST=... DB_USER=... DB_PASS=... script.sh", run='DB_HOST="mi servidor" DB_USER=ana bash "$1"',
         check='cat "$OUT" "$ERR" | grep -q DB_PASS && ! cat "$OUT" "$ERR" | grep -q DB_HOST && [ "$RC" -eq 1 ]'),
    dict(id=42, tarea="Espera hasta que exista el archivo FILE, revisando cada segundo, durante un máximo de SEGUNDOS; termina con "
                      "código 0 si apareció y con 1 si no.",
         uso="script.sh FILE SEGUNDOS", run='bash "$1" "$D/informe${S}final.txt" 3',
         check='[ "$RC" -eq 0 ]'),
    dict(id=43, tarea="Copia a DEST solo los archivos .txt de DIR y sus subcarpetas, conservando la estructura de carpetas.",
         uso="script.sh DIR DEST", run='bash "$1" "$D" "$DEST"',
         check='[ -f "$DEST/sub${S}carpeta/apuntes${S}de${S}clase.txt" ] && [ ! -e "$DEST/app.log" ]'),
    dict(id=44, tarea="Imprime las 2 primeras líneas de cada archivo .log de DIR (sin subcarpetas), y antes de cada bloque una línea "
                      "'== NOMBRE ==' con el nombre del archivo.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='grep -q "== .*error${S}del${S}servidor.log ==" "$OUT" && grep -q "ERROR primero" "$OUT"'),
    dict(id=45, tarea="Busca los enlaces simbólicos rotos dentro de DIR y sus subcarpetas, y borra cada uno.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ ! -L "$D/enlace${S}roto" ] && [ -L "$D/enlace${S}bueno" ]'),
    dict(id=46, tarea="Añade a FILE una línea con la fecha de hoy (AAAA-MM-DD) y el tamaño total de DIR en bytes, separados por un espacio.",
         uso="script.sh DIR FILE", run='bash "$1" "$D" "$DEST/historial${S}de${S}tamanos.txt"',
         check='grep -qE "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]+$" "$DEST/historial${S}de${S}tamanos.txt"'),
    dict(id=47, tarea="Imprime la última línea que contiene ERROR en el archivo FILE.",
         uso="script.sh FILE", run='bash "$1" "$D/error${S}del${S}servidor.log"',
         check='grep -q "ERROR tercero" "$OUT"'),
    dict(id=48, tarea="Para cada archivo .csv de DIR y sus subcarpetas, imprime 'NOMBRE: N filas', sin contar la línea de cabecera.",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='grep -qE "usuarios\\.csv: 2 filas" "$OUT"'),
    dict(id=49, tarea="Copia FILE a DEST; si en DEST ya existe un archivo con el mismo nombre, no lo sobrescribas: añade la fecha y la "
                      "hora al nombre de la copia nueva.",
         uso="script.sh FILE DEST", run='bash "$1" "$D/informe${S}final.txt" "$DEST"',
         check='[ "$(find "$DEST" -maxdepth 1 -name "*informe${S}final*" | wc -l)" -ge 2 ] && grep -q viejo "$DEST/informe${S}final.txt"'),
    dict(id=50, tarea="Borra las carpetas vacías que haya dentro de DIR (sin borrar DIR).",
         uso="script.sh DIR", run='bash "$1" "$D"',
         check='[ ! -d "$D/carpeta${S}sin${S}nada" ] && [ -d "$D/sub${S}carpeta" ] && [ -d "$D" ]'),
]

CLAUDE_IDS = list(range(1, 40, 2))  # 20 tareas, fijadas antes de generar

PROMPT = """Escribe un script de Bash para esta tarea de administración de sistemas.
Tarea: {tarea}
Uso: {uso}
Solo puedes usar bash y las herramientas de un Debian básico (coreutils, findutils, grep, sed, awk, tar, gzip, procps, util-linux).
Responde solo con el script completo dentro de un bloque ```bash, sin explicaciones."""

PROMPT_ARREGLO = """Este es tu script:
```bash
{script}
```
ShellCheck 0.11.0 da estos avisos:
{avisos}
Corrige el script para que ShellCheck no dé avisos. Responde solo con el script completo dentro de un bloque ```bash, sin explicaciones."""


def tareas_sh():
    """Genera el bash con una función run_N / check_N / pre_N por tarea."""
    lineas = ["# generado por tareas.py — no editar"]
    for t in T:
        n = t["id"]
        lineas.append(f"run_{n}() {{\n  {t['run']}\n}}")
        lineas.append(f"check_{n}() {{\n  {t['check']}\n}}")
        lineas.append(f"pre_{n}() {{\n  {t.get('pre', ':')}\n}}")
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    assert len(T) == 50 and [t["id"] for t in T] == list(range(1, 51))
    print(len(T), "tareas;", len(CLAUDE_IDS), "para Claude Code")
