# SALIDA — OpenTofu vs Pulumi (vídeo 339)

Generado 2026-10-08 00:20 UTC con `python correr.py`. OpenTofu v1.12.7 (HCL) y Pulumi v3.267.0 (Python), la misma infra con el proveedor de Docker.

## 1 · La misma infraestructura, dos lenguajes

### OpenTofu: main.tf (HCL)

`$ cat main.tf`

```
terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "tcp://dind:2375" }

resource "docker_network" "red" { name = "tienda-tf" }

resource "docker_image" "nginx" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "web-tf"
  image = docker_image.nginx.image_id
  networks_advanced {
    name = docker_network.red.name
  }
  ports {
    internal = 80
    external = 8080
  }
}
```

### Pulumi: __main__.py (Python)

`$ cat __main__.py`

```
import pulumi
import pulumi_docker as docker

red = docker.Network("red", name="tienda-pulumi")
img = docker.RemoteImage("nginx", name="nginx:1.29-alpine", keep_locally=True)
web = docker.Container("web", name="web-pulumi", image=img.image_id,
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=red.name)],
    ports=[docker.ContainerPortArgs(internal=80, external=8081)])
pulumi.export("contenedor", web.name)
```

### líneas de código

`$ wc -l`

```
OpenTofu (HCL): 25 líneas
Pulumi (Python): 9 líneas
```

## 2 · Preparar

### OpenTofu: tofu init

`$ tofu init`

```
- Finding kreuzwerker/docker versions matching "~> 3.0"...
- Installing kreuzwerker/docker v3.9.0...
- Installed kreuzwerker/docker v3.9.0 (signed, key ID 0DCE698927DAF8EC)
OpenTofu has been successfully initialized!
```

### Pulumi: login local + stack + config

`$ pulumi login file:// ; stack init ; config set`

```
Logged in to b2dba873ff1b as root (file:///w)
Created stack 'dev'
listo
```

## 3 · El plan antes de crear nada

### OpenTofu: tofu plan

`$ tofu plan`

```
# docker_container.web will be created
  # docker_image.nginx will be created
  # docker_network.red will be created
Plan: 3 to add, 0 to change, 0 to destroy.
```

### Pulumi: pulumi preview

`$ pulumi preview`

```
+  pulumi:pulumi:Stack tienda-dev create 
 +  docker:index:RemoteImage nginx create 
 +  docker:index:Network red create 
 +  docker:index:Container web create 
 +  pulumi:pulumi:Stack tienda-dev create 
Resources:
    + 4 to create
```

## 4 · Crear

### OpenTofu: tofu apply

`$ tofu apply -auto-approve`

```
docker_container.web: Creating...
docker_container.web: Creation complete after 0s [id=21bb64e7aa593bf58047a9f6022a752ab76b717da888eaa7faf74c521d0d47ae]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
(en 6 s)
```

### Pulumi: pulumi up

`$ pulumi up --yes`

```
Resources:
    + 4 created

Duration: 5s

warning: A new version of Pulumi is available. To upgrade from version '3.267.0' to '3.268.0', visit https://pulumi.com/docs/install/ for manual instructions and release notes.
(en 9 s)
```

### lo que hay en el Docker destino

`$ docker ps / network ls`

```
web-pulumi
web-tf
tienda-pulumi
tienda-tf
```

## 5 · El estado

### OpenTofu: dónde y cómo

`$ ls; head terraform.tfstate`

```
6089 terraform.tfstate
---
{
  "version": 4,
  "terraform_version": "1.12.7",
  "serial": 1,
  "lineage": "81907771-6e06-d937-4b15-c8b53d01f6ad",
  "outputs": {},
  "resources": [
    {
      "mode": "managed",
      "type": "docker_container",
      "name": "web",
      "provider": "provider[\"registry.opentofu.org/kreuzwerker/docker\"]",
      "instances": [
        {
          "schema_version": 2,
          "attributes":
```

### Pulumi: dónde y cómo

`$ ls .pulumi; stack export | head`

```
/w/.pulumi/backups/tienda/dev/dev.1791418823513439556.json
/w/.pulumi/stacks/tienda/dev.json
/w/.pulumi/history/tienda/dev/dev-1791418823512797605.checkpoint.json
---
{
    "version": 3,
    "deployment": {
        "manifest": {
            "time": "2026-10-08T00:20:23.46615162Z",
            "magic": "3de546644abd884104c0da6c4b4f579c66b2066fca3a62f46440e362d6fd706c",
            "version": "v3.267.0"
        },
        "secrets_providers": {
            "type": "passphrase",
            "state": {
                "salt": "v1:vK7MEMXntBg=:v1:vIJA0gD6YL4xHPcP:Nh
```

## 6 · Algo cambia por fuera (drift)

### borro el contenedor a mano

`$ docker rm -f web (en el dind)`

```
contenedor web borrado a mano
```

### OpenTofu: lo detecta

`$ tofu plan`

```
# docker_container.web will be created
Plan: 1 to add, 0 to change, 0 to destroy.
Note: You didn't use the -out option to save this plan, so OpenTofu can't
```

### Pulumi: lo detecta

`$ pulumi preview --refresh`

```
~  docker:index:Container web refreshing 
 ~  docker:index:Container web refresh 
 +  docker:index:Container web create 
Resources:
    + 1 to create
```

## 7 · Destruir

### OpenTofu: tofu destroy

`$ tofu destroy -auto-approve`

```
Destroy complete! Resources: 3 destroyed.
(apply+destroy en 8 s)
```

### Pulumi: pulumi destroy

`$ pulumi destroy --yes`

```
The resources in the stack have been deleted, but the history and configuration associated with the stack are still maintained. 
If you want to remove the stack completely, run `pulumi stack rm dev`.
warning: A new version of Pulumi is available. To upgrade from version '3.267.0' to '3.268.0', visit https://pulumi.com/docs/install/ for manual instructions and release notes.
```

### el Docker destino, vacío

`$ docker ps -a`

```
contenedores web: 0
```
