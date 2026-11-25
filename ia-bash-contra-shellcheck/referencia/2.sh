#!/bin/bash
tar -czf "$2/respaldo-$(date +%Y%m%d).tar.gz" -C "$1" .
