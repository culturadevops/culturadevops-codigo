#!/bin/bash
r=0; while IFS= read -r s; do [ -n "$s" ] || continue; if pgrep -x "$s" >/dev/null; then echo "$s: activo"; else echo "$s: caído"; r=1; fi; done < "$1"; exit $r
