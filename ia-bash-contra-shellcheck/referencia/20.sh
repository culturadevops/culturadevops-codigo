#!/bin/bash
find "$1" -type f -name "*.sh" -exec chmod +x {} +; find "$1" -type f -exec chmod o-w {} +
