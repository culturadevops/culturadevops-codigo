# -*- coding: utf-8 -*-
"""Banco del vídeo 409 «¿Vale la pena Azure en 2027?». Sin cuenta de Azure: lo que se practica gratis en local.
  · la CLI oficial (mcr.microsoft.com/azure-cli) en un contenedor;
  · Bicep: una cuenta de almacenamiento en Bicep, compilada a la plantilla ARM (JSON) que entiende Azure;
  · Azurite, el emulador oficial de Storage: crear un contenedor, subir un blob y listarlo con la misma CLI.
    python correr.py   -> SALIDA.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
NET = "lab-azure"
# cadena de conexión de desarrollo de Azurite (documentada por Microsoft, pública)
CONN = ("DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://azurite:10000/devstoreaccount1;")
BICEP = """param location string = resourceGroup().location
param nombre string = 'tiendafotos${uniqueString(resourceGroup().id)}'

resource cuenta 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: nombre
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

output id string = cuenta.id
"""


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "-w", "/work", "azcli", "bash", "-c", cmd])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    for c in ("azcli", "azurite"):
        run(["docker", "rm", "-f", c])
    run(["docker", "network", "rm", NET])
    run(["docker", "network", "create", NET])
    run(["docker", "run", "-d", "--name", "azurite", "--network", NET, "mcr.microsoft.com/azure-storage/azurite",
         "azurite-blob", "--blobHost", "0.0.0.0", "--skipApiVersionCheck"])
    run(["docker", "run", "-d", "--name", "azcli", "--network", NET, "mcr.microsoft.com/azure-cli",
         "bash", "-c", "mkdir -p /work && sleep infinity"])
    time.sleep(5)
    OUT.append(f"# SALIDA — Azure en local (vídeo 409)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
               "Sin cuenta de Azure: CLI oficial, Bicep y el emulador Azurite, todo en Docker.\n")

    OUT.append("## 1 · La CLI oficial, en un contenedor\n")
    bloque("versión", "az version", "az version --output table 2>/dev/null || az version")

    OUT.append("## 2 · Bicep: lo que escribes y lo que Azure recibe\n")
    ex(f"cat > tienda.bicep <<'EOF'\n{BICEP}EOF")
    bloque("instalar Bicep", "az bicep install; az bicep version", "az bicep install >/dev/null 2>&1; az bicep version")
    bloque("el fichero Bicep", "cat tienda.bicep; wc -l tienda.bicep", "cat tienda.bicep; wc -l tienda.bicep")
    bloque("compilarlo a la plantilla ARM", "az bicep build --file tienda.bicep; wc -l tienda.json",
           "az bicep build --file tienda.bicep && wc -l tienda.json && head -c 600 tienda.json")
    bloque("un error lo detecta al compilar", "(nombre mal escrito) az bicep build",
           "sed 's/cuenta.id/cuenta.idd/' tienda.bicep > roto.bicep && az bicep build --file roto.bicep 2>&1 | tail -3")

    OUT.append("## 3 · Azure Storage en local con Azurite\n")
    bloque("crear un contenedor", "az storage container create -n fotos --connection-string …",
           f"az storage container create -n fotos --connection-string '{CONN}' -o json")
    ex("echo 'hola desde azurite' > foto.txt")
    bloque("subir un blob", "az storage blob upload -c fotos -n foto.txt -f foto.txt …",
           f"az storage blob upload -c fotos -n foto.txt -f foto.txt --connection-string '{CONN}' --only-show-errors -o none && echo subido")
    bloque("listarlo", "az storage blob list -c fotos -o table …",
           f"az storage blob list -c fotos --connection-string '{CONN}' --query \"[].{{nombre:name, bytes:properties.contentLength}}\" -o table")
    bloque("descargarlo", "az storage blob download -c fotos -n foto.txt -f copia.txt …",
           f"az storage blob download -c fotos -n foto.txt -f copia.txt --connection-string '{CONN}' --only-show-errors -o none && cat copia.txt")

    OUT.append("## 4 · Lo que pesa la herramienta\n")
    bloque("tamaño de las imágenes", "docker image inspect -f {{.Size}}",
           "echo")  # se rellena desde fuera
    s1, _ = run(["docker", "image", "inspect", "-f", "{{.Size}}", "mcr.microsoft.com/azure-cli"])
    s2, _ = run(["docker", "image", "inspect", "-f", "{{.Size}}", "mcr.microsoft.com/azure-storage/azurite"])
    OUT[-1] = OUT[-1].replace("```\n\n```", f"```\nmcr.microsoft.com/azure-cli {s1}\nmcr.microsoft.com/azure-storage/azurite {s2}\n```")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    for c in ("azcli", "azurite"):
        run(["docker", "rm", "-f", c])
    run(["docker", "network", "rm", NET])
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
