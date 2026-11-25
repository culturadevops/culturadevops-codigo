$ git -C action log --oneline --decorate
8eb1cc4 (HEAD -> main, tag: v1) v1: lista archivos cambiados

$ cat workflow-etiqueta.yml workflow-sha.yml
      - uses: mi-org/action@v1
      - uses: mi-org/action@8eb1cc4aba0cd4a156f93c10258dc3a5568248d4   # v1

# antes del ataque, lo que ejecuta cada workflow:
  workflow-etiqueta.yml -> 8eb1cc4 -> echo "listando archivos cambiados..."
  workflow-sha.yml -> 8eb1cc4 -> echo "listando archivos cambiados..."

$ git -C action tag -f v1 HEAD   # quien controla el repo mueve la etiqueta
Updated tag 'v1' (was <sha>)
$ git -C action log --oneline --decorate
4ddc1a8 (HEAD -> main, tag: v1) actualiza dependencias
8eb1cc4 v1: lista archivos cambiados

# después del ataque, lo que ejecuta cada workflow:
  workflow-etiqueta.yml -> 4ddc1a8 -> echo "listando archivos cambiados..."; echo "(aquí el código malicioso imprimiría tus secretos)"
  workflow-sha.yml -> 8eb1cc4 -> echo "listando archivos cambiados..."

$ # ¿y si intento que otro commit tenga el mismo SHA?
$ git -C action cat-file -t 8eb1cc4aba0c
commit
  (un SHA es el hash del contenido: otro contenido da otro SHA)

$ grep -rnE "uses: [^.][^@]*@" repo/.github/workflows | grep -vE "@[0-9a-f]{40}"   # sin fijar por SHA
repo/.github/workflows/ci.yml:5:      - uses: actions/checkout@v4
repo/.github/workflows/ci.yml:6:      - uses: tj-actions/changed-files@v45
