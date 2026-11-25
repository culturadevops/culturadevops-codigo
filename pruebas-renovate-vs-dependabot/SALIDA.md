# SALIDA — Renovate vs Dependabot (vídeo 343)

Generado 2026-10-12 23:27 UTC con `python correr.py`. Dependabot con dependabot-cli en local (el motor de GitHub); Renovate con la plataforma local. Ninguno crea PR de verdad: se lee lo que abrirían.

## 1 · Versiones y el repositorio

### versiones

`$ dependabot --version; docker run renovate/renovate:latest renovate --version`

```
dependabot version v1.94.0
renovate 44.155.1
```

### package.json

`$ cat package.json`

```
{
  "name": "app",
  "version": "1.0.0",
  "dependencies": {
    "express": "4.17.1",
    "lodash": "4.17.15",
    "axios": "0.21.1"
  },
  "devDependencies": {
    "jest": "26.6.3",
    "eslint": "7.32.0"
  }
}
```

### requirements.txt

`$ cat requirements.txt`

```
requests==2.25.1
flask==1.1.2
urllib3==1.26.4
```

### Dockerfile

`$ cat Dockerfile`

```
FROM python:3.9-slim
COPY . /app
CMD ["python", "/app/main.py"]
```

## 2 · Por defecto

### Dependabot: una pasada por ecosistema

`$ dependabot update <ecosistema> lab/app --local repo`

```
[npm_and_yarn] 5 PR en 52 s
  express ( from 4.17.1 to 5.3.0 )
  lodash ( from 4.17.15 to 4.18.1 )
  axios ( from 0.21.1 to 1.20.0 )
  jest ( from 26.6.3 to 30.5.2 )
  eslint ( from 7.32.0 to 10.12.0 )
[pip] 3 PR en 10 s
  requests ( from 2.25.1 to 2.34.2 )
  flask ( from 1.1.2 to 3.1.3 )
  urllib3 ( from 1.26.4 to 2.8.0 )
[docker] 1 PR en 108 s
  python ( from 3.9-slim to 3.14-slim )

TOTAL: 9 PR · 169 s
```

### Renovate con config:recommended

`$ renovate --platform=local  (config:recommended)`

```
renovate/python-3.x
    python 3.9-slim → 3.15-slim (minor)
renovate/express-4.x
    express 4.17.1 → 4.22.3 (minor)
renovate/express-5.x
    express 4.17.1 → 5.3.0 (major)
renovate/lodash-monorepo
    lodash 4.17.15 → 4.18.1 (minor)
renovate/axios-0.x
    axios 0.21.1 → 0.34.0 (minor)
renovate/axios-1.x
    axios 0.21.1 → 1.20.0 (major)
renovate/major-jest-monorepo
    jest 26.6.3 → 30.5.2 (major)
renovate/major-eslint-monorepo
    eslint 7.32.0 → 10.12.0 (major)
renovate/requests-2.x
    requests ==2.25.1 → ==2.34.2 (minor)
renovate/flask-1.x
    flask ==1.1.2 → ==1.1.4 (patch)
renovate/flask-3.x
    flask ==1.1.2 → ==3.1.3 (major)
renovate/urllib3-1.x
    urllib3 ==1.26.4 → ==1.26.20 (patch)
renovate/urllib3-2.x
    urllib3 ==1.26.4 → ==2.8.0 (major)

TOTAL: 13 ramas · 8 s
```

## 3 · Agrupando

### Dependabot: un grupo con todo npm

`$ cat job-npm-grupo.yaml; dependabot update -f job-npm-grupo.yaml --local repo`

```
job:
  package-manager: npm_and_yarn
  allowed-updates:
    - update-type: all
  source:
    provider: github
    repo: lab/app
    directory: /
  dependency-groups:
    - name: todo-npm
      rules:
        patterns:
          - "*"

→ 1 PR en 57 s
  express ( from 4.17.1 to 5.3.0 ), lodash ( from 4.17.15 to 4.18.1 ), axios ( from 0.21.1 to 1.20.0 ), jest ( from 26....
```

### Renovate: menores y parches juntos

`$ RENOVATE_CONFIG={"extends": ["config:recommended"], "packageRules": [{"matchUpdateTypes": ["minor", "patch"], "groupName": "menores y parches"}]}`

```
renovate/menores-y-parches
    python 3.9-slim → 3.15-slim (minor)
    express 4.17.1 → 4.22.3 (minor)
    axios 0.21.1 → 0.34.0 (minor)
    requests ==2.25.1 → ==2.34.2 (minor)
    flask ==1.1.2 → ==1.1.4 (patch)
    urllib3 ==1.26.4 → ==1.26.20 (patch)
renovate/express-5.x
    express 4.17.1 → 5.3.0 (major)
renovate/lodash-monorepo
    lodash 4.17.15 → 4.18.1 (minor)
renovate/axios-1.x
    axios 0.21.1 → 1.20.0 (major)
renovate/major-jest-monorepo
    jest 26.6.3 → 30.5.2 (major)
renovate/major-eslint-monorepo
    eslint 7.32.0 → 10.12.0 (major)
renovate/flask-3.x
    flask ==1.1.2 → ==3.1.3 (major)
renovate/urllib3-2.x
    urllib3 ==1.26.4 → ==2.8.0 (major)

TOTAL: 8 ramas · 9 s
```

## 4 · Lo que descarga cada uno

### imágenes

`$ docker images | grep -E 'dependabot|renovate'`

```
ghcr.io/dependabot/dependabot-updater-docker:latest 1.49GB
ghcr.io/dependabot/dependabot-updater-npm:latest 2.14GB
ghcr.io/dependabot/dependabot-updater-pip:latest 2.74GB
ghcr.io/dependabot/proxy:latest 32.7MB
renovate/renovate:latest 1.92GB
```

## 5 · Anexo: una PR de Dependabot por dentro

### la primera de npm

`$ (salida de dependabot update npm_and_yarn: create_pull_request)`

```
pr-title: Bump express from 4.17.1 to 5.3.0

commit-message:
Bump express from 4.17.1 to 5.3.0

Bumps [express](https://github.com/expressjs/express) from 4.17.1 to 5.3.0.
- [Release notes](https://github.com/expressjs/express/releases)
- [Changelog](https://github.com/expressjs/express/blob/master/History.md)
- [Commits](https://github.com/expressjs/express/compare/4.17.1...v5.3.0)
```
