# -*- coding: utf-8 -*-
"""Soluciones de referencia (escritas a mano) para probar el BANCO antes de medir a las IA.
Si una de estas falla, el fallo es del check, no de la IA. Las 50 tienen que pasar en control y con espacios."""
import os

R = {
 1: 'mkdir -p "$2"; for f in "$1"/*.log; do [ -f "$f" ] && cp -- "$f" "$2/"; done',
 2: 'tar -czf "$2/respaldo-$(date +%Y%m%d).tar.gz" -C "$1" .',
 3: 'f=$1; [ -f "$f.5" ] && rm -f -- "$f.5"; for i in 4 3 2 1; do [ -f "$f.$i" ] && mv -- "$f.$i" "$f.$((i+1))"; done; [ -f "$f" ] && mv -- "$f" "$f.1"; : > "$f"',
 4: 'find "$1" -type f -mtime +30 -delete',
 5: 'for f in "$1"/*.txt; do [ -f "$f" ] && printf "%s: %s\\n" "$(basename -- "$f")" "$(wc -l < "$f")"; done',
 6: 'find "$1" -type f -name "*.log" -exec cat {} + | grep -c ERROR',
 7: 'for f in "$1"/*.log; do [ -f "$f" ] && gzip -- "$f"; done',
 8: 'for f in "$1"/*.*; do [ -f "$f" ] || continue; b=${f%.*}; e=${f##*.}; l=$(printf "%s" "$e" | tr "[:upper:]" "[:lower:]"); [ "$e" != "$l" ] && mv -- "$f" "$b.$l"; done; true',
 9: 'cd "$1" || exit 1; find . -maxdepth 1 -type f ! -name SHA256SUMS -printf "%P\\0" | xargs -0 sha256sum > SHA256SUMS',
 10: 'k=$(du -sk "$1" | cut -f1); echo "$k"; [ "$k" -gt "$2" ] && exit 2; exit 0',
 11: 'for f in "$1"/*.*; do [ -f "$f" ] || continue; e=${f##*.}; e=${e,,}; mkdir -p "$1/$e"; mv -- "$f" "$1/$e/"; done',
 12: 'find "$1" -type f -printf "%s\\t%p\\n" | sort -rn | head -3 | cut -f2-',
 13: 'tail -n +2 "$1" | cut -d, -f2',
 14: 'r=0; while IFS= read -r s; do [ -n "$s" ] || continue; if pgrep -x "$s" >/dev/null; then echo "$s: activo"; else echo "$s: caído"; r=1; fi; done < "$1"; exit $r',
 15: 'for f in "$1"/*.txt; do [ -f "$f" ] || continue; d=$(date -r "$f" +%Y-%m-%d); mv -- "$f" "$(dirname -- "$f")/${d}_$(basename -- "$f")"; done',
 16: 'n=$(find "$1" -type f \\( -name "*.tmp" -o -name "*.bak" \\) -print -delete | wc -l); echo "$n"',
 17: 'cd "$1" || exit 1; find . -type f -print0 | while IFS= read -r -d "" f; do t="$2/$f"; if [ ! -e "$t" ] || [ "$f" -nt "$t" ]; then mkdir -p -- "$(dirname -- "$t")"; cp -p -- "$f" "$t"; fi; done',
 18: 'find "$1" -maxdepth 1 -type f -name "*.log" -size +100k -exec truncate -s 0 {} +',
 19: 'find "$1" -type f -exec sha256sum {} + | sort | uniq -w64 --all-repeated=separate | cut -c67-',
 20: 'find "$1" -type f -name "*.sh" -exec chmod +x {} +; find "$1" -type f -exec chmod o-w {} +',
 21: 'log=$1; shift; "$@" 2>&1 | while IFS= read -r l; do printf "[%s] %s\\n" "$(date "+%F %T")" "$l"; done >> "$log"',
 22: 'for i in 1 2 3; do "$@"; rc=$?; [ $rc -eq 0 ] && exit 0; [ $i -lt 3 ] && sleep 1; done; exit $rc',
 23: 'exec 9>"$1"; flock -n 9 || exit 1; echo trabajando >> "$2"',
 24: 'awk "{print \\$1}" "$1" | sort | uniq -c | sort -rn | head -5 | awk "{print \\$1, \\$2}"',
 25: 'grep -v "^#" "$1" | grep "^$2=" | head -1 | cut -d= -f2-',
 26: 'awk -F: "\\$7==\\"/bin/bash\\"{print \\$1}" /etc/passwd',
 27: 'r=0; while IFS= read -r p; do [ -n "$p" ] || continue; [ -e "$p" ] || { echo "FALTA: $p"; r=1; }; done < "$1"; exit $r',
 28: 'find "$1" -type f -name "*.conf" -print0 | while IFS= read -r -d "" f; do if grep -qF -- "$2" "$f"; then cp -- "$f" "$f.orig"; sed -i "s|$2|$3|g" "$f"; fi; done',
 29: 'find "$1" -type f -mtime -1',
 30: 'tar -czf "$2/respaldo-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$1" .; ls -1t "$2"/*.tar.gz | tail -n +4 | while IFS= read -r f; do rm -f -- "$f"; done',
 31: 'du -sh "$1"/*/ | sort -rh',
 32: 'for f in "$1"/*.txt; do [ -f "$f" ] && sed -i "s/\\r$//" "$f"; done',
 33: 'mkdir -p "$2"; find "$1" -type f -name "*.log" -print0 | sort -z | xargs -0 cat > "$2/todo.log"',
 34: 'u=$(df -P "$1" | awk "NR==2{gsub(/%/,\\"\\",\\$5); print \\$5}"); if [ "$u" -gt "$2" ]; then echo ALERTA; else echo OK; fi',
 35: 'while IFS= read -r u; do [ -n "$u" ] && echo "useradd -m $u"; done < "$1"',
 36: 'for f in "$1"/*.tar.gz; do [ -f "$f" ] || continue; d=${f%.tar.gz}; mkdir -p -- "$d"; tar -xzf "$f" -C "$d"; done',
 37: 'find "$1" -type f -name "*.*" -printf "%f\\n" | sed "s/.*\\.//" | sort | uniq -c | sort -rn | awk "{print \\$2, \\$1}"',
 38: 'n=$1; log=$2; shift 2; if ! pgrep -x "$n" >/dev/null; then "$@" & echo reiniciado >> "$log"; fi',
 39: 'for f in "$1"/*.log; do [ -f "$f" ] || continue; m=$(date -r "$f" +%Y-%m); mkdir -p "$1/$m"; mv -- "$f" "$1/$m/"; done',
 40: 'for f in "$1"/*.txt; do [ -f "$f" ] && sed -i "s/[[:space:]]*$//" "$f"; done',
 41: 'r=0; for v in DB_HOST DB_USER DB_PASS; do [ -n "${!v:-}" ] || { echo "falta $v"; r=1; }; done; exit $r',
 42: 'for ((i=0;i<$2;i++)); do [ -e "$1" ] && exit 0; sleep 1; done; [ -e "$1" ]',
 43: 'cd "$1" || exit 1; find . -type f -name "*.txt" -print0 | while IFS= read -r -d "" f; do mkdir -p -- "$2/$(dirname -- "$f")"; cp -- "$f" "$2/$f"; done',
 44: 'for f in "$1"/*.log; do [ -f "$f" ] || continue; echo "== $(basename -- "$f") =="; head -n 2 -- "$f"; done',
 45: 'find "$1" -xtype l -delete',
 46: 'echo "$(date +%F) $(du -sb "$1" | cut -f1)" >> "$2"',
 47: 'grep ERROR "$1" | tail -n 1',
 48: 'find "$1" -type f -name "*.csv" -print0 | while IFS= read -r -d "" f; do echo "$(basename -- "$f"): $(( $(wc -l < "$f") - 1 )) filas"; done',
 49: 'b=$(basename -- "$1"); t="$2/$b"; [ -e "$t" ] && t="$2/$(date +%Y%m%d-%H%M%S)_$b"; cp -- "$1" "$t"',
 50: 'find "$1" -mindepth 1 -type d -empty -delete',
}

if __name__ == "__main__":
    aqui = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(aqui, "referencia"), exist_ok=True)
    for n, cuerpo in R.items():
        with open(os.path.join(aqui, "referencia", f"{n}.sh"), "w", encoding="utf-8", newline="\n") as f:
            f.write("#!/bin/bash\n" + cuerpo + "\n")
    print(len(R), "referencias escritas")
