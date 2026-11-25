# Salida ejecutada — vídeo 236 «Escribe un proveedor de OpenTofu y entiende el apply»

> Corrida del 2026-09-10 en `banco-tofu` (golang:1.26-bookworm + **OpenTofu 1.12.6** instalado
> como binario suelto, que es precisamente una de las cosas que enseña la serie).
> Reproducible con `docker build -t banco-tofu . && docker run --rm -v "$PWD:/lab" -w /lab banco-tofu bash /lab/demo.sh`.

El proveedor gestiona algo **tangible y comprobable**: un fichero en disco con un contenido.
Se eligió a propósito para poder tocarlo por fuera y ver el desvío.

---

## 1 · El proveedor es un binario aparte

```
   tamaño: 25163885 bytes
   y si lo ejecuto suelto: This binary is a plugin. These are not meant to be executed directly.
```

**24 MB para gestionar un fichero de texto.** Y el propio binario te dice que no lo ejecutes:
no es un programa, es un servidor que espera a que alguien le hable.

## 2 · ⛔ El primer intento falla. Se enseña tal cual

```
$ tofu init
- Finding lab/ficherito versions matching "0.1.0"...
╷
│ Error: Failed to query available provider packages
│
│ Could not retrieve the list of available versions for provider
│ lab/ficherito: provider registry registry.opentofu.org does not have a
│ provider named registry.opentofu.org/lab/ficherito
╵
   >>> salió con 1
```

**El binario está ahí, compilado, en el directorio de al lado. Y OpenTofu se va a internet a
buscarlo.** El error no dice «lo tienes mal puesto»: dice que no existe. Esa es la fricción real.

## 3 · La instalación que sí funciona

```
~/.terraform.d/plugins/registry.opentofu.org/lab/ficherito/0.1.0/linux_amd64/
                        └─ registro ─┘  └ns┘ └─ nombre ─┘ └ver┘ └── plataforma ──┘
```
Y el fichero dentro tiene que llamarse `terraform-provider-ficherito_v0.1.0`.

⚠️ **La ruta lleva dentro el registro, el espacio de nombres, el nombre, la versión y la
arquitectura.** Si te equivocas en cualquiera de las cinco partes, el error es el mismo de arriba:
«no existe», nunca «está mal puesto».

```
- Installing lab/ficherito v0.1.0...
OpenTofu has been successfully initialized!
```

## 4 · Plan

```
  # ficherito_fichero.saludo will be created
  + resource "ficherito_fichero" "saludo" {
      + contenido = "hola desde el proveedor"
      + id        = (known after apply)
      + ruta      = "/lab/salida/hola.txt"
    }
Plan: 1 to add, 0 to change, 0 to destroy.
```

## 5 · 🥇 EL HALLAZGO: el proveedor arranca CUATRO veces en un solo apply

Con `ps` no se pillan los dos procesos porque el apply tarda cero segundos. La traza del
protocolo sí lo demuestra, y enseña algo que no esperaba:

```
   «starting plugin»:       4
   «plugin process exited»: 4
   PIDs distintos:          4
     pid=5083   pid=5096   pid=5112   pid=5126

   y cada uno con SU socket:
     address=/tmp/plugin2317477569
     address=/tmp/plugin2349115104
     address=/tmp/plugin3625330388
     address=/tmp/plugin920841543

   using plugin: version=6      <- la versión del protocolo
```

**Un solo `tofu apply` arrancó el proveedor cuatro veces y lo mató cuatro veces**, cada vez con
un socket nuevo. Las fases:

```
   starting plugin  ->  tf_rpc=GetProviderSchema
   starting plugin  ->  tf_rpc=PlanResourceChange
   starting plugin  ->  tf_rpc=PlanResourceChange
                        tf_rpc=ApplyResourceChange
```

Las llamadas completas del protocolo en esa corrida:

```
   ValidateProviderConfig
   GetProviderSchema
   GetResourceIdentitySchemas
   ConfigureProvider
   ValidateResourceConfig
   PlanResourceChange
   ApplyResourceChange
```

🥇 **Consecuencia práctica que mucha gente no sabe:** tu proveedor **no puede guardar nada entre
llamadas**. Ni una caché, ni una conexión reutilizada, ni una variable. Muere entre fase y fase.
Todo lo que tenga que sobrevivir va al **estado**, y por eso el estado es como es.

## 6 · El fichero existe de verdad

```
   contenido en disco: hola desde el proveedor
```

## 7 · El estado: lo que OpenTofu cree que hay

```
     direccion: ficherito_fichero.saludo
     tipo:      ficherito_fichero
       contenido  = 'hola desde el proveedor'
       id         = '/lab/salida/hola.txt'
       ruta       = '/lab/salida/hola.txt'
```

## 8 · 🥇 El desvío: toco el fichero por fuera

```
$ echo "me lo cambio a mano" > /lab/salida/hola.txt
$ tofu plan
  # ficherito_fichero.saludo will be updated in-place
  ~ resource "ficherito_fichero" "saludo" {
      ~ contenido = <<-EOT
Plan: 0 to add, 1 to change, 0 to destroy.
```

**De aquí sale la respuesta a la pregunta del vídeo.** OpenTofu no adivina nada: antes de
planificar llama a `Read` del proveedor, que va al mundo real y devuelve cómo está la cosa. Luego
compara tres cosas —lo que dice el mundo real, lo que dice el estado y lo que dice tu
configuración— y de ahí salen crear, actualizar o destruir.

⛔ **Y por eso un proveedor mal escrito no detecta desvíos nunca.** Si `Read` devuelve lo que ya
dice el estado en vez de mirar el mundo real, todo parece siempre correcto. El fallo no da error:
da silencio.

## 9 · Si borro el fichero, lo planifica como creación

```
  # ficherito_fichero.saludo will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

Eso es el `RemoveResource` del `Read`: «esto ya no está», y OpenTofu lo saca del estado.

## 10 · Destroy, comprobado

```
ficherito_fichero.saludo: Destruction complete after 0s
Destroy complete! Resources: 1 destroyed.
   ¿queda el fichero? no
   recursos en el estado: 0
```

---

## ⛔ Fallos de esta corrida, los dos míos

1. **`go build` desde el directorio equivocado.** `go: go.mod file not found`. El banco moría en
   el paso 1.
2. **`ctx` declarado y sin usar** en `main()`. Go se niega a compilar por eso — que es
   exactamente lo que cuenta el vídeo «Go no te deja compilar por una variable sin usar» del
   canal hermano. Me pasó a mí escribiendo esto.

## ⛔ Lo que NO es este proveedor

- **No es de producción, y hay que decirlo sin adornos.** No maneja importación, ni renombrados,
  ni reintentos, ni credenciales, ni las validaciones que necesita cualquier proveedor serio.
- **No se publica en el registro.** El objetivo es ver el mecanismo, no distribuir nada.
- **No hay concurrencia real**: un recurso, un fichero. Con cientos de recursos entran en juego
  el grafo de dependencias y el paralelismo, que no se miden aquí.
