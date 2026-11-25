# generado por tareas.py — no editar
run_1() {
  bash "$1" "$D" "$DEST"
}
check_1() {
  [ -f "$DEST/app.log" ] && [ -f "$DEST/error${S}del${S}servidor.log" ] && [ -f "$DEST/registro${S}antiguo.log" ]
}
pre_1() {
  :
}
run_2() {
  bash "$1" "$D" "$DEST"
}
check_2() {
  f=$(find "$DEST" -name "respaldo-*.tar.gz" -mmin -10 | head -1); [ -n "$f" ] && tar -tzf "$f" | grep -q "informe${S}final.txt"
}
pre_2() {
  :
}
run_3() {
  bash "$1" "$D/error${S}del${S}servidor.log"
}
check_3() {
  F="$D/error${S}del${S}servidor.log"; [ -s "$F.1" ] && [ -f "$F" ] && [ ! -s "$F" ]
}
pre_3() {
  :
}
run_4() {
  bash "$1" "$D"
}
check_4() {
  [ ! -e "$D/copia${S}vieja.bak" ] && [ ! -e "$D/registro${S}antiguo.log" ] && [ -f "$D/app.log" ] && [ -f "$D/informe${S}final.txt" ]
}
pre_4() {
  :
}
run_5() {
  bash "$1" "$D"
}
check_5() {
  grep -qE "informe${S}final\.txt: ?3$" "$OUT"
}
pre_5() {
  :
}
run_6() {
  bash "$1" "$D"
}
check_6() {
  [ "$(tr -d "[:space:]" < "$OUT")" = 7 ]
}
pre_6() {
  :
}
run_7() {
  bash "$1" "$D"
}
check_7() {
  [ -f "$D/error${S}del${S}servidor.log.gz" ] && [ -f "$D/app.log.gz" ]
}
pre_7() {
  :
}
run_8() {
  bash "$1" "$D"
}
check_8() {
  [ -f "$D/foto${S}de${S}perfil.jpg" ] && [ ! -e "$D/foto${S}de${S}perfil.JPG" ]
}
pre_8() {
  :
}
run_9() {
  bash "$1" "$D"
}
check_9() {
  (cd "$D" && sha256sum -c SHA256SUMS 2>/dev/null | grep -q "informe${S}final.txt: OK")
}
pre_9() {
  :
}
run_10() {
  bash "$1" "$D" 1
}
check_10() {
  [ "$RC" -eq 2 ] && grep -qE "^[0-9]+" "$OUT"
}
pre_10() {
  :
}
run_11() {
  bash "$1" "$D"
}
check_11() {
  [ -f "$D/txt/informe${S}final.txt" ] && [ -f "$D/log/error${S}del${S}servidor.log" ]
}
pre_11() {
  :
}
run_12() {
  bash "$1" "$D"
}
check_12() {
  head -1 "$OUT" | grep -q "registro${S}antiguo.log"
}
pre_12() {
  :
}
run_13() {
  bash "$1" "$D/sub${S}carpeta/usuarios.csv"
}
check_13() {
  grep -qx "ana@ejemplo.com" "$OUT" && grep -qx "luis@ejemplo.com" "$OUT" && ! grep -q correo "$OUT"
}
pre_13() {
  :
}
run_14() {
  bash "$1" "$D/servicios${S}a${S}vigilar.txt"
}
check_14() {
  grep -q "sleep: activo" "$OUT" && grep -qE "noexiste-xyz: ca(í|i)do" "$OUT" && [ "$RC" -eq 1 ]
}
pre_14() {
  sleep 300 >/dev/null 2>&1 &
}
run_15() {
  bash "$1" "$D"
}
check_15() {
  find "$D" -maxdepth 1 -name "????-??-??_informe${S}final.txt" | grep -q .
}
pre_15() {
  :
}
run_16() {
  bash "$1" "$D"
}
check_16() {
  [ ! -e "$D/copia${S}vieja.bak" ] && [ ! -e "$D/sub${S}carpeta/temp${S}de${S}trabajo.tmp" ] && [ -f "$D/app.log" ] && grep -q 2 "$OUT"
}
pre_16() {
  :
}
run_17() {
  bash "$1" "$D" "$DEST"
}
check_17() {
  [ -f "$DEST/sub${S}carpeta/otro${S}archivo.log" ] && [ -f "$DEST/app.log" ]
}
pre_17() {
  :
}
run_18() {
  bash "$1" "$D"
}
check_18() {
  [ -f "$D/registro${S}antiguo.log" ] && [ ! -s "$D/registro${S}antiguo.log" ] && [ -s "$D/app.log" ]
}
pre_18() {
  :
}
run_19() {
  bash "$1" "$D"
}
check_19() {
  grep -q "copia${S}del${S}informe.txt" "$OUT" && grep -q "informe${S}final.txt" "$OUT"
}
pre_19() {
  :
}
run_20() {
  bash "$1" "$D"
}
check_20() {
  [ -x "$D/sub${S}carpeta/mi${S}script.sh" ]
}
pre_20() {
  :
}
run_21() {
  bash "$1" "$D/salida${S}del${S}comando.log" ls "$D"
}
check_21() {
  grep -qE "^\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\] ?informe" "$D/salida${S}del${S}comando.log"
}
pre_21() {
  :
}
run_22() {
  bash "$1" test -f "$D/informe${S}final.txt"
}
check_22() {
  [ "$RC" -eq 0 ]
}
pre_22() {
  :
}
run_23() {
  bash "$1" "$D/mi${S}tarea.lock" "$D/registro${S}de${S}tarea.txt"
}
check_23() {
  grep -q trabajando "$D/registro${S}de${S}tarea.txt"
}
pre_23() {
  :
}
run_24() {
  bash "$1" "$D/acceso${S}del${S}sitio.log"
}
check_24() {
  head -1 "$OUT" | grep -q "10\.0\.0\.1$"
}
pre_24() {
  :
}
run_25() {
  bash "$1" "$D/config.conf" ruta_datos
}
check_25() {
  grep -qx "/srv/datos${S}de${S}app" "$OUT"
}
pre_25() {
  :
}
run_26() {
  bash "$1"
}
check_26() {
  grep -qx root "$OUT"
}
pre_26() {
  :
}
run_27() {
  bash "$1" "$D/rutas.txt"
}
check_27() {
  grep -q "FALTA: .*no${S}existe.txt" "$OUT" && ! grep -q "FALTA: .*informe" "$OUT" && [ "$RC" -eq 1 ]
}
pre_27() {
  :
}
run_28() {
  bash "$1" "$D" "puerto=8080" "puerto=9090"
}
check_28() {
  grep -q "puerto=9090" "$D/config.conf" && [ -f "$D/config.conf.orig" ]
}
pre_28() {
  :
}
run_29() {
  bash "$1" "$D"
}
check_29() {
  grep -q "informe${S}final.txt" "$OUT" && ! grep -q "copia${S}vieja" "$OUT"
}
pre_29() {
  :
}
run_30() {
  bash "$1" "$D" "$DEST"
}
check_30() {
  n=$(find "$DEST" -name "*.tar.gz" | wc -l); f=$(find "$DEST" -name "*.tar.gz" -mmin -10 | head -1); [ "$n" -le 3 ] && [ -n "$f" ] && tar -tzf "$f" | grep -q "informe${S}final.txt"
}
pre_30() {
  :
}
run_31() {
  bash "$1" "$D"
}
check_31() {
  grep -q "sub${S}carpeta" "$OUT"
}
pre_31() {
  :
}
run_32() {
  bash "$1" "$D"
}
check_32() {
  ! grep -q "$(printf "\r")" "$D/notas${S}de${S}junio.txt" && [ "$(wc -l < "$D/notas${S}de${S}junio.txt")" -eq 2 ]
}
pre_32() {
  :
}
run_33() {
  bash "$1" "$D" "$DEST"
}
check_33() {
  grep -q "linea del otro archivo" "$DEST/todo.log" && grep -q "linea de app" "$DEST/todo.log"
}
pre_33() {
  :
}
run_34() {
  bash "$1" "$D" 0
}
check_34() {
  grep -q ALERTA "$OUT"
}
pre_34() {
  :
}
run_35() {
  bash "$1" "$D/nuevos${S}usuarios.txt"
}
check_35() {
  grep -q "useradd.*ana" "$OUT" && grep -q "useradd.*luis" "$OUT"
}
pre_35() {
  :
}
run_36() {
  bash "$1" "$D"
}
check_36() {
  find "$D/paquete${S}de${S}prueba" -name dentro.txt 2>/dev/null | grep -q .
}
pre_36() {
  :
}
run_37() {
  bash "$1" "$D"
}
check_37() {
  grep -qE "^\.?log:? +[0-9]+$" "$OUT"
}
pre_37() {
  :
}
run_38() {
  bash "$1" noexiste-xyz "$D/registro${S}reinicios.log" sleep 1
}
check_38() {
  grep -q reiniciado "$D/registro${S}reinicios.log"
}
pre_38() {
  :
}
run_39() {
  bash "$1" "$D"
}
check_39() {
  find "$D" -mindepth 2 -path "*/20[0-9][0-9]-[0-9][0-9]/*" -name "error${S}del${S}servidor.log" | grep -q .
}
pre_39() {
  :
}
run_40() {
  bash "$1" "$D"
}
check_40() {
  ! grep -q " $" "$D/informe${S}final.txt" && [ "$(wc -l < "$D/informe${S}final.txt")" -eq 3 ]
}
pre_40() {
  :
}
run_41() {
  DB_HOST="mi servidor" DB_USER=ana bash "$1"
}
check_41() {
  cat "$OUT" "$ERR" | grep -q DB_PASS && ! cat "$OUT" "$ERR" | grep -q DB_HOST && [ "$RC" -eq 1 ]
}
pre_41() {
  :
}
run_42() {
  bash "$1" "$D/informe${S}final.txt" 3
}
check_42() {
  [ "$RC" -eq 0 ]
}
pre_42() {
  :
}
run_43() {
  bash "$1" "$D" "$DEST"
}
check_43() {
  [ -f "$DEST/sub${S}carpeta/apuntes${S}de${S}clase.txt" ] && [ ! -e "$DEST/app.log" ]
}
pre_43() {
  :
}
run_44() {
  bash "$1" "$D"
}
check_44() {
  grep -q "== .*error${S}del${S}servidor.log ==" "$OUT" && grep -q "ERROR primero" "$OUT"
}
pre_44() {
  :
}
run_45() {
  bash "$1" "$D"
}
check_45() {
  [ ! -L "$D/enlace${S}roto" ] && [ -L "$D/enlace${S}bueno" ]
}
pre_45() {
  :
}
run_46() {
  bash "$1" "$D" "$DEST/historial${S}de${S}tamanos.txt"
}
check_46() {
  grep -qE "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]+$" "$DEST/historial${S}de${S}tamanos.txt"
}
pre_46() {
  :
}
run_47() {
  bash "$1" "$D/error${S}del${S}servidor.log"
}
check_47() {
  grep -q "ERROR tercero" "$OUT"
}
pre_47() {
  :
}
run_48() {
  bash "$1" "$D"
}
check_48() {
  grep -qE "usuarios\.csv: 2 filas" "$OUT"
}
pre_48() {
  :
}
run_49() {
  bash "$1" "$D/informe${S}final.txt" "$DEST"
}
check_49() {
  [ "$(find "$DEST" -maxdepth 1 -name "*informe${S}final*" | wc -l)" -ge 2 ] && grep -q viejo "$DEST/informe${S}final.txt"
}
pre_49() {
  :
}
run_50() {
  bash "$1" "$D"
}
check_50() {
  [ ! -d "$D/carpeta${S}sin${S}nada" ] && [ -d "$D/sub${S}carpeta" ] && [ -d "$D" ]
}
pre_50() {
  :
}
