#!/bin/bash
r=0; for v in DB_HOST DB_USER DB_PASS; do [ -n "${!v:-}" ] || { echo "falta $v"; r=1; }; done; exit $r
