#!/usr/bin/env bash
# Demo del vídeo 466 «El ataque a tj-actions» — se EJECUTA y su salida va a SALIDA.md.
# Lo que se reproduce es el MECANISMO, con repos locales de mentira (nada de GitHub):
#   1) una «action» con su etiqueta v1 y un workflow que la usa por etiqueta y otro por SHA;
#   2) alguien con acceso al repo de la action mueve la etiqueta v1 a un commit nuevo (git tag -f);
#   3) qué código recibe cada workflow después;
#   4) cómo encontrar en tus workflows las actions que no están fijadas por SHA.
# Todo dentro de un directorio temporal. El «commit malicioso» solo imprime un texto.
set -u
T=$(mktemp -d)
cd "$T"
export GIT_AUTHOR_NAME=demo GIT_AUTHOR_EMAIL=demo@ejemplo.invalid GIT_COMMITTER_NAME=demo GIT_COMMITTER_EMAIL=demo@ejemplo.invalid
git init -q -b main action && cd action && git config core.autocrlf false
echo 'echo "listando archivos cambiados..."' > entrypoint.sh
git add . && git commit -q -m "v1: lista archivos cambiados"
git tag v1
BUENO=$(git rev-parse HEAD)
cd ..

echo '$ git -C action log --oneline --decorate'
git -C action log --oneline --decorate | sed 's/^\([0-9a-f]\{7\}\)/\1/'
echo
echo '$ cat workflow-etiqueta.yml workflow-sha.yml'
echo "      - uses: mi-org/action@v1" | tee workflow-etiqueta.yml
echo "      - uses: mi-org/action@$BUENO   # v1" | tee workflow-sha.yml
echo

resolver() {   # lo que haría el runner: resolver la referencia y leer el código de ESE commit
  ref=$(sed -E 's/.*@([^ ]+).*/\1/' "$1")
  sha=$(git -C action rev-parse "$ref^{commit}")
  echo "  $1 -> ${sha:0:7} -> $(git -C action show "$sha:entrypoint.sh")"
}
echo '# antes del ataque, lo que ejecuta cada workflow:'
resolver workflow-etiqueta.yml
resolver workflow-sha.yml
echo

cd action
echo 'echo "listando archivos cambiados..."; echo "(aquí el código malicioso imprimiría tus secretos)"' > entrypoint.sh
git commit -q -am "actualiza dependencias"
echo '$ git -C action tag -f v1 HEAD   # quien controla el repo mueve la etiqueta'
git tag -f v1 HEAD 2>&1 | sed 's/[0-9a-f]\{7,\}/<sha>/g'
cd ..
echo '$ git -C action log --oneline --decorate'
git -C action log --oneline --decorate
echo
echo '# después del ataque, lo que ejecuta cada workflow:'
resolver workflow-etiqueta.yml
resolver workflow-sha.yml
echo

echo '$ # ¿y si intento que otro commit tenga el mismo SHA?'
echo "$ git -C action cat-file -t ${BUENO:0:12}"
git -C action cat-file -t "${BUENO:0:12}"
echo "  (un SHA es el hash del contenido: otro contenido da otro SHA)"
echo

mkdir -p repo/.github/workflows
cat > repo/.github/workflows/ci.yml <<'EOF'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tj-actions/changed-files@v45
      - uses: actions/setup-go@d35c59abb061a4a6fb18e82ac0862c26744d6ab5 # v5.5.0
      - uses: ./acciones/local
EOF
echo '$ grep -rnE "uses: [^.][^@]*@" repo/.github/workflows | grep -vE "@[0-9a-f]{40}"   # sin fijar por SHA'
grep -rnE "uses: [^.][^@]*@" repo/.github/workflows | grep -vE "@[0-9a-f]{40}"
cd / && rm -rf "$T"
