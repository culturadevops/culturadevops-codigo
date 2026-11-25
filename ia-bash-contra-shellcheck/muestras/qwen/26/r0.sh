#!/bin/bash
cut -d: -f1 /etc/passwd | grep '^:' | cut -d: -f7 | grep '/bin/bash' | cut -d: -f1
