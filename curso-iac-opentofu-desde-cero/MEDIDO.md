# Medido en esta máquina · 2026-08-25

Todo lo que afirma el curso (vídeo 126) sale de aquí. Ninguna cifra ni salida viene de la
documentación de OpenTofu.

    OpenTofu v1.12.5 (windows_amd64) · proveedor kreuzwerker/docker ~> 3.0 · Docker 29.6.2

⚠️ En Windows hay que declarar el host del proveedor: `npipe:////./pipe/docker_engine`. Sin eso
busca `/var/run/docker.sock`, que no existe.

---

## L02 · el ciclo, cronometrado

Cinco pasadas cada uno, en milisegundos:

| | 1 | 2 | 3 | 4 | 5 | media |
|---|---:|---:|---:|---:|---:|---:|
| `plan` sin cambios | 601 | 581 | 575 | 583 | 596 | **587** |
| `apply` sin cambios | 593 | 591 | 570 | 577 | 589 | **584** |
| `apply` creando de cero | 1145 | 1095 | 1120 | 1114 | 1109 | **1116** |

**Plan y apply sin cambios cuestan lo mismo** (587 contra 584). Tiene sentido: los dos hacen el
mismo refresco contra lo real, y luego uno no aplica nada. Un `apply` sin cambios no es gratis.

---

## L03 · el estado

Para una declaración de **26 líneas** con dos recursos:

| | |
|---|---|
| tamaño | 4.765 bytes |
| versión del formato | 4 |
| atributos guardados del contenedor | **72** |
| atributos que escribí yo | 4 |

Escribes cuatro campos y el estado guarda setenta y dos. Ahí está la respuesta a por qué el
estado no es «un fichero de configuración»: es el inventario de lo que existe de verdad.

---

## L06 · `count` contra `for_each` — la lección que más vale

Tres contenedores, `alfa`, `beta`, `gamma`. Se quita **el del medio** en los dos:

| | plan resultante |
|---|---|
| `count` | `Plan: 1 to add, 0 to change, 2 to destroy` |
| `for_each` | `Plan: 0 to add, 0 to change, 1 to destroy` |

Con `count`, `web[1]` pasa a ser gamma, así que hay que reemplazarlo, y `web[2]` sobra. **Se
destruyen dos contenedores que nadie tocó.** Con `for_each` el nombre es `web["beta"]` y quitarlo
no mueve a los demás.

---

## L08 · importar algo que ya existe

Contenedor creado a mano con `docker run`, sin OpenTofu. El arco completo, tal cual salió:

1. `tofu import` con el identificador **corto** → falla.
2. Con el largo (`873541debd97…`) → `Import successful!`
3. Pero el plan dice **`must be replaced`**. Lo fuerzan `env` y `ports`.
4. Añado `ip = "::"` → sigue queriendo reemplazar: el real tiene **dos** enlaces, `0.0.0.0` y
   `::`, porque Docker publica en IPv4 y en IPv6 por defecto.
5. Con **dos bloques** de `ports` → `Plan: 0 to add, 1 to change, 0 to destroy`. Ya no reemplaza.
6. `apply` → y después `No changes. Your infrastructure matches the configuration.`
7. El contenedor sigue siendo `873541debd97…`: **nunca se recreó**.

Lo caro de importar no es el mandato: es cuadrar la declaración con lo que ya existe, atributo a
atributo, hasta que el plan diga que no hay nada que hacer.

---

## L10 · secretos y cifrado

Con `random_password` de 24 caracteres:

| | |
|---|---|
| en pantalla | `aviso = <sensitive>` |
| `tofu output aviso` | lo enseña entero |
| en `terraform.tfstate` | **en claro**: `result: {BFFs*L1)AN>+=>)znmZ<BQg` |

Y el estado **se marca a sí mismo**:
```
sensitive_attributes: [[{"type":"get_attr","value":"bcrypt_hash"}],
                       [{"type":"get_attr","value":"result"}]]
```
Sabe que es un secreto, lo etiqueta como secreto, y lo guarda legible igual.

### Encender el cifrado sobre un estado que ya existe NO es un interruptor
Con `enforced = true` a secas:
```
Error acquiring the state lock
Error message: failed to write backup file: encountered unencrypted payload
without unencrypted method configured
```
Se niega hasta a respaldarlo. Hace falta declarar un método `unencrypted` como `fallback` para
la migración, y quitarlo después. Con eso:

- apariciones del secreto en claro en el estado: **0**
- el estado empieza por `key_provider.pbkdf2.clave` con **600.000 iteraciones**

---

## Tropiezos del montaje (para el guion)

1. **`variable "frase" { type = string, sensitive = true }` no compila.** HCL no admite dos
   argumentos en un bloque de una línea: «Single-line block syntax can include only one argument
   definition». Hay que abrirlo en varias líneas.
2. **El identificador corto de Docker no sirve para importar.** Y el error no dice «usa el
   largo»: habla de la región o el punto de acceso del proveedor.
3. **El fallo del cifrado aparece como un error de BLOQUEO del estado**, no como un error de
   cifrado. El motivo real está en la segunda línea.
