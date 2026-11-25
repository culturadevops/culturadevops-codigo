# SALIDA — Renovate (vídeo 329)

Generado 2026-10-07 21:52 UTC con `python correr.py`. Gitea (gitea/gitea:latest) + renovate/renovate:latest en Docker.

### versión de Renovate

`$ docker run renovate/renovate:latest renovate --version`

```
44.145.1
```

## 1 · El repositorio: dependencias de 2021 en tres ecosistemas

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

## 2 · Primera pasada, sin configuración: onboarding

### renovate (1.ª pasada)

`$ docker run renovate/renovate (platform=gitea)`

```
INFO: Repository started (repository=dev/app)
INFO: Dependency extraction complete (repository=dev/app, baseBranch=main)
INFO: Onboarding PR created (repository=dev/app)
INFO: Repository finished (repository=dev/app)
(tardó 10 s)
```

### PR abiertas

`$ GET /repos/dev/app/pulls`

```
#1   Configure Renovate
(1 PR)
```

### la PR de onboarding (recorte)

`$ cuerpo de la PR`

```
Welcome to [Renovate](https://github.com/renovatebot/renovate)! This is an onboarding PR to help you understand and configure settings before regular Pull Requests begin.

🚦 To activate Renovate, merge this Pull Request. To disable Renovate, simply close this Pull Request unmerged.

📚 See our [Reading List](https://docs.renovatebot.com/reading-list/) for relevant documentation you may be interested in reading.

🔡 Do you want to change how Renovate upgrades your dependencies? Add your custom config to `renovate.json` in this branch. Renovate will update the Pull Request description the next time it runs.



---
### Detected Package Files

 * `Dockerfile` (dockerfile)
 * `package.json` (npm)
 * `requirements.txt` (pip_requirements)

### What to Expect

With your current configuration, Renovate will create 10 Pull Requests, up to a maximum of 13 over time (see [docs for `prConcurrentLimit`](https://docs.renovatebot.com/configuration-options/#prconcurrentlimit)):

<details>
<summary>Update dependency flask to v1.1.4</summary>

  - Schedule: ["at any time"]
  - Branch name: `renovate/flask-1.x`
  - Merge into: `main`
  - Upgrade [flask](https://github.com/pallets/flask) to `==1.1.4`


</details>

<details>
<summary>Update dependency urllib3 to v1.26.20</summary>

  - Schedule: ["at any time"]
  - Branch name: `renovate/urllib3-1.x`
  - Merge into: `main`
  - Upgrade [urllib3](https://github.com/urllib3/urllib3) to `==1.26.20`


</details>

<details>
<summary>Update dependency axios to v0.34.0</summary>

  - Schedule: ["at any time"]
  - Branch name: `renovate/axios-0.x`
  - Merge into: `main`
  - Upgrade [axios](https://github.com/axios/axios) to `sha512-CkOmqy7BaT4VC9+wRUmSM3LVwCkKK3UYc7koEqIHWRpOTJypwdNctaVOgnOjhHP3599Ubq2K8KqYwfC7c8NdPQ==`


</details>

<details>
<summary>Update dependency express to v4.22.3</summary>

  - Schedule: ["at any time"]
  - Branch name: `renovate/express-4.x`
  - Merge into: `main`
  - Upgrade [express](https://github.com/expressjs/express) to `sha512-Bdcs4+3qlpVlx2NRn6fgX2Ue2/gGRaPeawebgclM0ERSCqDpA+owF1fdPwjJUTAJWMTuAaxjDf+hzb0/4eKvvw==`


</details>

<details>
<summary>Update dependency lodash to v4.18.1</summary>

  - Schedule: ["at any time"]
  - Branch name: `renovate/lodash-4.x`
  - Merge into: `main`
  - Upgrade [lodash](https://github.com/lodash/lodash) to `sha512-dMInicTPVE8d1e5otfwmmjlxkZoUpiVLwyeTdUsi/Caj/gfzzblBcCE5sRHV/AsjuCmxWrte2TNGSYuCeCq+0Q==`


</details>

<details>
<summary>Update dependency requests to v2.34.
```

### fusionar la PR de onboarding

`$ merge #1`

```
200
```

## 3 · Segunda pasada, con config:recommended: el límite por hora

### renovate.json que trae la PR

`$ cat renovate.json`

```
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json"
}
```

### renovate (2.ª pasada)

`$ docker run renovate/renovate`

```
INFO: Repository started (repository=dev/app)
INFO: Dependency extraction complete (repository=dev/app, baseBranch=main)
INFO: PR created (repository=dev/app, branch=renovate/flask-1.x)
INFO: PR created (repository=dev/app, branch=renovate/urllib3-1.x)
INFO: Repository finished (repository=dev/app)
(tardó 10 s)
```

### PR abiertas

`$ GET /repos/dev/app/pulls`

```
#2   Update dependency flask to v1.1.4
#3   Update dependency urllib3 to v1.26.20
(2 PR)
```

## 4 · Sin límite: todas las PR

### renovate.json

`$ cat renovate.json`

```
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended"
  ],
  "prHourlyLimit": 0,
  "prConcurrentLimit": 0
}
```

### renovate (sin límite)

`$ docker run renovate/renovate`

```
INFO: Repository started (repository=dev/app-todo)
INFO: Dependency extraction complete (repository=dev/app-todo, baseBranch=main)
INFO: PR created (repository=dev/app-todo, branch=renovate/flask-1.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/urllib3-1.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/axios-0.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/express-4.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/lodash-monorepo)
INFO: PR created (repository=dev/app-todo, branch=renovate/requests-2.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/python-3.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/axios-1.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/major-eslint-monorepo)
INFO: PR created (repository=dev/app-todo, branch=renovate/express-5.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/flask-3.x)
INFO: PR created (repository=dev/app-todo, branch=renovate/major-jest-monorepo)
INFO: PR created (repository=dev/app-todo, branch=renovate/urllib3-2.x)
INFO: Repository finished (repository=dev/app-todo)
(tardó 17 s)
```

### PR abiertas

`$ GET /repos/dev/app-todo/pulls`

```
#1   Update dependency flask to v1.1.4
#2   Update dependency urllib3 to v1.26.20
#3   Update dependency axios to v0.34.0
#4   Update dependency express to v4.22.3
#5   Update dependency lodash to v4.18.1
#6   Update dependency requests to v2.34.2
#7   Update python Docker tag to v3.14
#8   Update dependency axios to v1
#9   Update dependency eslint to v10
#10  Update dependency express to v5
#11  Update dependency flask to v3
#12  Update dependency jest to v30
#13  Update dependency urllib3 to v2
(13 PR)
```

### diff de la PR #4

`$ GET .../pulls/4.diff`

```
diff --git a/package.json b/package.json
index 2b10a56..4fc64a0 100644
--- a/package.json
+++ b/package.json
@@ -2,7 +2,7 @@
   "name": "app",
   "version": "1.0.0",
   "dependencies": {
-    "express": "4.17.1",
+    "express": "4.22.3",
     "lodash": "4.17.15",
     "axios": "0.21.1"
   },
```

## 5 · Cerrar una PR sin fusionarla: ¿la vuelve a abrir?

### cerrar sin fusionar

`$ PATCH .../pulls/9 state=closed`

```
#9 Update dependency eslint to v10 → cerrada
```

### renovate otra vez

`$ docker run renovate/renovate`

```
INFO: Repository started (repository=dev/app-todo)
INFO: Dependency extraction complete (repository=dev/app-todo, baseBranch=main)
INFO: Repository finished (repository=dev/app-todo)
(tardó 12 s)
```

### PR abiertas

`$ GET /repos/dev/app-todo/pulls`

```
#1   Update dependency flask to v1.1.4
#2   Update dependency urllib3 to v1.26.20
#3   Update dependency axios to v0.34.0
#4   Update dependency express to v4.22.3
#5   Update dependency lodash to v4.18.1
#6   Update dependency requests to v2.34.2
#7   Update python Docker tag to v3.14
#8   Update dependency axios to v1
#10  Update dependency express to v5
#11  Update dependency flask to v3
#12  Update dependency jest to v30
#13  Update dependency urllib3 to v2
(12 PR)
```

### comentarios en la #9

`$ GET .../issues/9/comments`

```
### Renovate Ignore Notification

Because you closed this PR without merging, Renovate will ignore this update. You will not get PRs for *any* future `10.x` releases. But if you manually upgrade to `10.x` then Renovate will re-enable `minor` and `patch` updates automatically.

If you accidentally closed this PR, or if you changed your mind: rename this PR to get a fresh replacement PR.
```

## 6 · Agrupando: menores y parches juntos, mayores bajo aprobación

### renovate.json

`$ cat renovate.json`

```
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended"
  ],
  "prHourlyLimit": 0,
  "prConcurrentLimit": 0,
  "packageRules": [
    {
      "matchUpdateTypes": [
        "minor",
        "patch"
      ],
      "groupName": "menores y parches"
    },
    {
      "matchUpdateTypes": [
        "major"
      ],
      "dependencyDashboardApproval": true
    }
  ]
}
```

### renovate (agrupado)

`$ docker run renovate/renovate`

```
INFO: Repository started (repository=dev/app-agrupado)
INFO: Dependency extraction complete (repository=dev/app-agrupado, baseBranch=main)
INFO: PR created (repository=dev/app-agrupado, branch=renovate/menores-y-parches)
INFO: Repository finished (repository=dev/app-agrupado)
(tardó 9 s)
```

### PR abiertas

`$ GET /repos/dev/app-agrupado/pulls`

```
#1   Update menores y parches
(1 PR)
```

### la PR agrupada (recorte del cuerpo)

`$ cuerpo de la PR`

```
This PR contains the following updates:

| Package | Change | [Age](https://docs.renovatebot.com/merge-confidence/) | [Confidence](https://docs.renovatebot.com/merge-confidence/) | Type | Update |
|---|---|---|---|---|---|
| [axios](https://axios-http.com) ([source](https://github.com/axios/axios)) | [`0.21.1` → `0.34.0`](https://renovatebot.com/diffs/npm/axios/0.21.1/0.34.0) | ![age](https://developer.mend.io/api/mc/badges/age/npm/axios/0.34.0?slim=true) | ![confidence](https://developer.mend.io/api/mc/badges/confidence/npm/axios/0.21.1/0.34.0?slim=true) | dependencies | minor |
| [express](https://expressjs.com/) ([source](https://github.com/expressjs/express)) | [`4.17.1` → `4.22.3`](https://renovatebot.com/diffs/npm/express/4.17.1/4.22.3) | ![age](https://developer.mend.io/api/mc/badges/age/npm/express/4.22.3?slim=true) | ![confidence](https://developer.mend.io/api/mc/badges/confidence/npm/express/4.17.1/4.22.3?slim=true) | dependencies | minor |
| [flask](https://github.com/pallets/flask) ([changelog](https://flask.palletsprojects.com/page/changes/)) | `==1.1.2` → `==1.1.4` | ![age](https://developer.mend.io/api/mc/badges/age/pypi/flask/1.1.4?slim=true) | ![confidence](https://developer.mend.io/api/mc/badges/confidence/pypi/flask/1.1.2/1.1.4?slim=true) |  | patch |
| [lodash](https://lodash.com/) ([source](https://github.com/lodash/lodash)) | [`4.17.15` → `4.18.1`](https://renovatebot.com/diffs/npm/lodash/4.17.15/4.18.1) | ![age](https://developer.mend.io/api/mc/badges/age/npm/lodash/4.18.1?slim=true) | ![confidence](https://developer.mend.io/api/mc/badges/confidence/npm/lodash/4.17.15/4.18.1?slim=true) | dependencies | minor |
| [python](https://hub.docker.com/_/python) ([source](https://github.com/docker-library/python)) | `3.9-slim` → `3.14-slim` | ![age](https://developer.mend.io/api/mc/badges/age/docker/python/3.14?slim=true) | ![confidence](https://developer.mend.io/api/mc/badges/confidence/docker/python/3.9/3.14?slim=true) | final | minor |
| [requests](https://github.com/psf/requests) ([changelog](https://github.com/psf/requests/blob/master/HISTORY.md)) | `==2.25.1` → `==2.34.2` | ![age](https://developer.mend.io/api/mc/badges/age/pypi/requests/2.34.2?slim=true) | ![confidence](https://developer.mend.io/api/mc/badges/confidence/pypi/requests/2.25.1/2.34.2?slim=true) |  | minor |
| [urllib3](https://github.com/urllib3/urllib3) ([changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst)) | `==1.26.4` → `==1.26.20` | ![age](https://dev
```

### el panel: mayores esperando aprobación

`$ issue #2`

```
This issue lists Renovate updates and detected dependencies. Read the [Dependency Dashboard](https://docs.renovatebot.com/key-concepts/dashboard/) docs to learn more.

## Repository Problems

Renovate tried to run on this repository, but found these problems.

 - ⚠️ WARN: No github.com token has been configured. Skipping release notes retrieval

## Pending Approval

The following branches are pending approval. To create them, click on a checkbox below.

 - [ ] <!-- approve-branch=renovate/axios-1.x -->Update dependency axios to v1
 - [ ] <!-- approve-branch=renovate/major-eslint-monorepo -->Update dependency eslint to v10
 - [ ] <!-- approve-branch=renovate/express-5.x -->Update dependency express to v5
 - [ ] <!-- approve-branch=renovate/flask-3.x -->Update dependency flask to v3
 - [ ] <!-- approve-branch=renovate/major-jest-monorepo -->Update dependency jest to v30
 - [ ] <!-- approve-branch=renovate/urllib3-2.x -->Update dependency urllib3 to v2
 - [ ] <!-- approve-all-pending-prs -->🔐 **Create all pending approval PRs at once** 🔐

## Open

The following updates have all been created. To force a retry/rebase of any, click on a checkbox below.

 - [ ] <!-- rebase-branch=renovate/menores-y-parches -->[Update menores y parches](pulls/1) (`axios`, `express`, `flask`, `lodash`, `python`, `requests`, `urllib3`)

## Detected Dependencies

<details><summary>dockerfile (1)</summary>
<blockquote>

<details><summary>Dockerfile (1)</summary>

 - `python 3.9-slim` → [Updates: `3.14-slim`]

</details>

</blockquote>
</details>

<details><summary>npm (1)</summary>
<blockquote>

<details><summary>package.json (5)</summary>

 - `express 4.17.1` → [Updates: `4.22.3`, `5.2.1`]
 - `lodash 4.17.15` → [Updates: `4.18.1`]
 - `axios 0.21.1` → [Updates: `0.34.0`, `1.20.0`]
 - `jest 26.6.3` → [Updates: `30.5.2`]
 - `eslint 7.32.0` → [Updates: `10.12.0`]

</details>

</blockquote>
</details>

<details><summary>pip_requirements (1)</summary>
<blockquote>

<details><summary>requirements.txt (3)</summary>

 - `requests ==2.25.1` → [Updates: `==2.34.2`]
 - `flask ==1.1.2` → [Updates: `==1.1.4`, `==3.1.3`]
 - `urllib3 ==1.26.4` → [Updates: `==1.26.20`, `==2.8.0`]

</details>

</blockquote>
</details>
```
