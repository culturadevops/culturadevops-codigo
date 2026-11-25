$ cat malo/.github/workflows/ci.yml
on: pull_request_target
permissions: write-all
jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - uses: tj-actions/changed-files@v45
      - run: make test
      - run: curl -H "Authorization: token ghp_EJEMPLOxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" https://api.github.com/user
      - run: echo "${{ secrets.DEPLOY_KEY }}"

$ python auditar.py malo
malo/.github/workflows/ci.yml: 5 hallazgo(s)
  [CICD-SEC-4 Poisoned Pipeline Execution] pull_request_target + checkout del código del PR: el código ajeno corre con tus secretos
  [CICD-SEC-5 Insufficient PBAC] permisos de escritura para todo (o sin declarar)
  [CICD-SEC-3 Dependency Chain Abuse] action de terceros fijada por etiqueta, no por SHA
  [CICD-SEC-6 Insufficient Credential Hygiene] token escrito en el YAML o secreto impreso en el log
  [CICD-SEC-7 Insecure System Configuration] runner propio ejecutando código de pull requests
(código de salida: 1)

$ cat bueno/.github/workflows/ci.yml
on: pull_request
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@08eba0b27e820071cde6df949e0beb9ba4906955 # v4.3.0
      - run: make test

$ python auditar.py bueno
bueno/.github/workflows/ci.yml: 0 hallazgo(s)
(código de salida: 0)

$ wc -l auditar.py
32
