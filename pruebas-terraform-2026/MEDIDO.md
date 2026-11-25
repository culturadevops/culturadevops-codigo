# Medido en esta máquina · 2026-09-13 · curso «Terraform 2026»

Todo lo que afirma el curso sale de aquí. Ninguna cifra ni salida viene de la documentación.
Cada `salida-*.txt` de las subcarpetas es la salida literal, sin retocar.

    Terraform v1.16.2 (windows_amd64) · kreuzwerker/docker v3.9.0 · hashicorp/http v3.6.2
    Docker 29.6.2 · imagen nginx:1.29-alpine

⚠️ En Windows el proveedor necesita `host = "npipe:////./pipe/docker_engine"`.
⚠️ `crono.sh` hace CINCO pasadas: una sola no es un dato.

---

## L01 · primer apply (`01-primer-apply/`)

| | 1 | 2 | 3 | 4 | 5 | media |
|---|---:|---:|---:|---:|---:|---:|
| `plan` sin cambios | 653 | 667 | 655 | 645 | 669 | **657 ms** |
| `apply` sin cambios | 733 | 716 | 690 | 733 | 699 | **714 ms** |
| `destroy` + `apply` de cero | 7230 | 7338 | 7084 | 6938 | 7172 | **7152 ms** |
| `validate` | 189 | 184 | 181 | 179 | 179 | **182 ms** |

- `init` la primera vez: 3,0 s (baja el proveedor 3.9.0 y crea `.terraform.lock.hcl`).
- `apply`: `docker_image.web: Creation complete after 6s` + contenedor 1 s. `curl` → HTTP 200.
- ⚠️ **`destroy` también borra la imagen descargada** (`keep_locally` es `false` por omisión):
  por eso el «de cero» cuesta 7 s y no 1 — vuelve a bajar nginx cada vez.

## L02 · leer el plan (`salida-01-cambios.txt`, `salida-02-plan-guardado.txt`)

| cambio en el código | plan |
|---|---|
| puerto 8080 → 8081 | `-/+` · `external = 8080 -> 8081 # forces replacement` · 1 add, 1 destroy |
| nombre `curso-web` → `curso-web2` | `# forces replacement` · 1 add, 1 destroy |
| `restart = "always"` | `~ update in-place` · 0 add, 1 change, 0 destroy |

- El plan de crear el contenedor enseña **41** líneas de atributo; en el código escribí 3.
- Plan guardado con `-out`, alguien aplica otro cambio antes → `Error: Saved plan is stale`.
- `lifecycle { create_before_destroy = true }` + cambio de puerto → `+/- create replacement and
  then destroy`… y el apply FALLA: `Conflict. The container name "/plan-web" is already in use`.
  El viejo sigue `Up` (sin corte). Con un nombre que cambia (`plan-web-8131`): crea el nuevo,
  destruye el `deposed object` y `1 added, 1 destroyed` (`02-plan/salida-02-create-before-destroy.txt`).
- `plan -detailed-exitcode`: sin cambios **0** · con cambio **2** · con error de sintaxis **1**.
  (Sin la opción, un plan con cambios también sale con 0.)
- `show -json` de un plan guardado (puerto + create_before_destroy): `docker_container.web
  ['create', 'delete']` · `docker_image.web ['no-op']` · 15.649 bytes. `plan -destroy` → `0 to add, 0 to change, 2 to destroy`.
- `init` deja `.terraform/` = **66 MB**; el proveedor `terraform-provider-docker_v3.9.0.exe` =
  **68.402.688 bytes**. Un segundo `apply` sin tocar nada → `No changes` · `0 added, 0 changed, 0 destroyed`.

## L03 · el estado (`salida-01-apply.txt`, `salida-03-*.txt`)

- `terraform.tfstate`: **4.842 bytes**, formato **4**, `terraform_version 1.16.2`.
- Atributos guardados: contenedor **72**, imagen **11**. En el código escribí 3 + 1.
- El estado por dentro: `mode managed`, `type`, `name`, y el `id` real de Docker
  (`02a34fa12a5fc64cfd9a2a75…`). `serial` 68 → **69 tras un `apply` SIN cambios** (lo reescribe igual).
- 🔥 **Borro `terraform.tfstate`** → `plan`: `2 to add` (cree que no existe nada) → `apply`:
  la imagen «se crea» en 0 s y el contenedor **falla**: `Conflict. The container name "/curso-web"
  is already in use`. El contenedor real seguía `Up`. Devuelvo el estado → `No changes`.
- `terraform state rm docker_container.web` → `Successfully removed 1 resource instance(s).`,
  el contenedor sigue `Up`, y el siguiente plan dice `will be created` (`salida-03-estado.txt`).
- 🔥 **Un `terraform plan` BORRÓ un contenedor parado** (`must_run = true`, por omisión):

      plan -refresh=false | antes: Exited (0) | después: Exited (0)
      plan (normal)       | antes: Exited (0) | después: <NO EXISTE>
      plan -refresh-only  | antes: Exited (0) | después: <NO EXISTE>

  Lo hace el proveedor de Docker al refrescar, no Terraform en sí. Repetido tres veces.
- `docker rm` por fuera → `plan -refresh-only`: `Objects have changed outside of Terraform` ·
  `docker_container.web has been deleted`.
- Bloqueo: con un `apply` esperando confirmación, el segundo `plan` →
  `Error: Error acquiring the state lock` (existe `.terraform.tfstate.lock.info`, 221 bytes).

## L04 · variables y secretos (`04-variables/`, `04b-efimera/`)

- `-var puerto=ochenta` → `a number is required`.
- `-var puerto=80` → sale MI mensaje de la `validation`.
- `-var entorno=prod` → `entorno solo puede ser dev, pre o pro.`
- Sin valor y sin terminal → `Error: No value for required variable`.
- **Precedencia medida** (puerto):

      solo default                 8090
      terraform.tfvars             8091
      tfvars + TF_VAR_puerto=8092  8091   ← la variable de entorno PIERDE contra el fichero
      + zz.auto.tfvars             8094
      + -var puerto=8093           8093   ← -var gana a todo

- `sensitive = true` con `Sup3rS3creta-2026`: plan y output enseñan `(sensitive value)`, pero
  `terraform output clave` la enseña, `-raw` también, y **está 2 veces en texto claro en el
  estado** (líneas 8 y 54). `docker inspect` también la enseña.
- Output SIN `sensitive` que usa `var.clave_bd` → `Error: Output refers to sensitive values`.
- Orden en la línea de órdenes: `-var-file=pro.tfvars -var puerto=8093` → 8093;
  `-var puerto=8093 -var-file=pro.tfvars` → **8095** (gana lo de la derecha).
- `terraform console`: `local.nombre` → `"web-pre"`, `var.clave_bd` → `(sensitive value)`,
  `nonsensitive(var.clave_bd)` → `"Sup3rS3creta-2026"` (`salida-04-extra.txt`).
- `ephemeral = true` usada en `env` → `Error: Invalid use of ephemeral value … because it is
  not a write-only attribute and must be persisted to state.`

## L05 · repetir y dependencias (`05-repetir/`, `05b-paralelo/`, `05c-dependencias/`)

- Quito `beta` (el del medio) de `["alfa","beta","gamma"]`:
  - `count`: `con_count[1] must be replaced` (`count-beta -> count-gamma`) y `con_count[2]
    will be destroyed` → **gamma se destruye y se recrea sin que nadie la tocara**.
  - `for_each`: solo `con_foreach["beta"] will be destroyed`.
- Crear 12 contenedores, 5 pasadas:

      -parallelism=1      7139 ms
      por omisión (10)    3155 ms
      -parallelism=20     2859 ms

- Red con nombre en TEXTO literal: crear 5/5 bien, destruir 5/5 bien… pero en la salida
  **Terraform empieza a borrar la red ANTES que el contenedor**, en paralelo; sale bien porque
  el proveedor reintenta (`Destruction complete after 2s`). Con REFERENCIA
  (`docker_network.red.name`) primero el contenedor y después la red, y `terraform graph`
  enseña la arista `docker_container.web -> docker_network.red`, que con texto no existe.

- `for_each` sobre `map(number)` `{tienda=8141, blog=8142}`: dos webs, HTTP 200 las dos,
  direcciones `docker_container.web["blog"]`/`["tienda"]`. Cambiar solo el puerto de blog →
  solo `web["blog"] must be replaced`. `depends_on = [docker_network.red]` → `terraform graph`
  dibuja `docker_container.web -> docker_network.red` (`05d-mapa/salida-05-mapa.txt`).

## L06 · módulos y lock (`06-modulos/`)

- Añadir `module` sin `init` → `Error: Module not installed`.
- Dos llamadas al mismo módulo local: 4 recursos, direcciones `module.tienda.docker_container.web`.
- `.terraform.lock.hcl`: versión `3.9.0`, restricción `~> 3.0`, **1 hash `h1:`** (el de mi
  plataforma) y **13 `zh:`**. `providers lock -platform=windows_amd64 -platform=linux_amd64` → 2 `h1:`.
- Restricción `~> 2.0` con el lock en 3.9.0 → `locked provider … 3.9.0 does not match
  configured version constraint ~> 2.0; must use terraform init -upgrade`.

- `terraform providers` enseña el árbol: raíz, `module.tienda` y `module.blog`, cada uno con `~> 3.0`.
- 🔥 Módulo SIN `keep_locally` usado dos veces → `destroy -target=module.blog`: borra el contenedor
  y FALLA la imagen: `unable to delete nginx:1.29-alpine (must be forced) - container 887c6fe9a3b5
  is using its referenced image` · `Warning: Applied changes may be incomplete`. Tienda sigue `Up`
  (`salida-06-imagen-compartida.txt`). Dos módulos gestionando la MISMA imagen.
- `~> 3.6.0` + `init -upgrade` → instala **3.6.2** y el lock pasa a 3.6.2; volver a `~> 3.0` + `-upgrade` → 3.9.0.

## L07 · cambiar sin destruir (`07-refactor/`)

- Renombrar `docker_container.web` → `.tienda` sin `moved`: 1 add, 1 destroy.
  Con `moved {}`: `has moved to`, 0/0/0, **mismo id** `253975feae06` antes y después.
- **De `count` a `for_each`** (alfa, beta, gamma): sin `moved` → `3 to add, 0 to change, 3 to destroy`.
  Con tres `moved` (`[0]`→`["alfa"]`, `[1]`→`["beta"]`, `[2]`→`["gamma"]`) → `0/0/0`, y los ids
  `1c4c90aa1e05 · c852265da867 · 64dac876c52d` idénticos antes y después (`05-repetir/salida-07-count-a-foreach.txt`).
- `import {}` + `plan -generate-config-out=generado.tf` sobre un `docker run -e MODO=produccion`:
  1. Sin `provider = docker` en el bloque → falla buscando `registry.terraform.io/hashicorp/docker`.
  2. Con él → genera **73 líneas**… y el plan dice `must be replaced` · `Warning: this will
     destroy the imported resource`. **El generador no escribió el `env`.**
  3. Una vez generado, `provider` en el `import` ya no se permite (`Invalid import provider argument`).
  4. Añadir `env` a mano sigue forzando reemplazo (tras importar, el estado no trae `env`).
  5. Con `lifecycle { ignore_changes = [env] }` → `1 to import, 0 to add, 1 to change, 0 to destroy`.
  6. Apply → `1 imported`; el contenedor sigue siendo `d34135838117`, `MODO=produccion` intacto,
     y después `No changes`.
- Import con el id CORTO de `docker ps` (`b4715229da4e`) → `Error: Cannot import non-existent remote
  object`. Con el LARGO de `docker inspect` sí lo encuentra… y, con un contenedor SIN `-e` mío, el plan
  también dice `this will destroy the imported resource`: es el atributo `env` entero (`07b-id-corto/salida-07-id-corto.txt`).
- Quitar el recurso del código sin `removed` → `will be destroyed`. Con `removed { lifecycle {
  destroy = false } }` → `will no longer be managed by Terraform, but will not be destroyed`,
  y el contenedor sigue `Up`.

## L08 · pruebas y CI (`08-pruebas/`, `09-query/`)

- `check` con `data "http"` sin la web levantada: en `plan` normal es **Warning** y sale con 0;
  en **`terraform test` falla el test**. Se arregla con `expect_failures = [check.la_web_responde]`.
- `terraform test`: `Success! 3 passed, 0 failed.` y no deja contenedores.
- 5 pasadas: **mock_provider 193 ms** · **Docker de verdad 2076 ms**.
- ⚠️ Mi primera medición salió mal: `-filter=tests/simulado.tftest.hcl` (barra `/`) en Windows
  no encuentra el fichero y tardaba 91 ms sin ejecutar nada. Y lo grave:
  `-filter` a un fichero que no existe → **`Success! 0 passed, 0 failed.` con código de salida 0**.
- `fmt -check` sobre un fichero mal sangrado → código **3**. `validate` → 0.
- `validate` caza `Reference to undeclared resource` (docker_image.wbe) y `Unsupported argument`
  (`puertos`), código 1, sin hablar con Docker (`08b-validate/salida-08-validate.txt`).
- `terraform query` (nuevo) con `list "docker_container"` → `The provider kreuzwerker/docker does
  not support list resource "docker_container".`
