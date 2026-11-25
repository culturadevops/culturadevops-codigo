#!/bin/bash
grep ERROR "$1" | tail -n 1
