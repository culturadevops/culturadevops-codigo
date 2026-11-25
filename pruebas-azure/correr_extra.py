# -*- coding: utf-8 -*-
"""Banco extra del vídeo 409. Sin cuenta de Azure, todo en Docker:
  · el linter de Bicep avisa de un parámetro que nadie usa;
  · decompilar: de la plantilla ARM (JSON) de vuelta a Bicep;
  · Azurite: un blob privado no se lee sin permiso; con un SAS de solo lectura, sí; y el SAS no deja escribir.
    python correr_extra.py   -> SALIDA-extra.md
"""
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
NET = "lab-azure"
CONN = ("DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://azurite:10000/devstoreaccount1;")
URL = "http://azurite:10000/devstoreaccount1/fotos/foto.txt"
FIJA = """resource cuenta 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'tiendafotos2027'
  location: 'eastus'
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}
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
    run(["docker", "network", "create", NET])
    run(["docker", "run", "-d", "--name", "azurite", "--network", NET, "mcr.microsoft.com/azure-storage/azurite",
         "azurite-blob", "--blobHost", "0.0.0.0", "--skipApiVersionCheck"])
    run(["docker", "run", "-d", "--name", "azcli", "--network", NET, "mcr.microsoft.com/azure-cli",
         "bash", "-c", "mkdir -p /work && sleep infinity"])
    time.sleep(5)
    ex("az bicep install >/dev/null 2>&1")
    OUT.append(f"# SALIDA extra — Azure en local (vídeo 409)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra.py`.\n")

    OUT.append("## 1 · El linter de Bicep\n")
    ex(f"cat > fija.bicep <<'EOF'\nparam entorno string\n{FIJA}EOF")
    bloque("un parámetro que nadie usa", "az bicep lint --file fija.bicep",
           "az bicep lint --file fija.bicep 2>&1 | grep -v 'update(s) available' | grep .")

    OUT.append("## 2 · De ARM a Bicep\n")
    ex("cat > t.bicep <<'EOF'\n" + FIJA.replace("'eastus'", "resourceGroup().location") + "EOF\naz bicep build --file t.bicep && mv t.json plantilla.json && rm t.bicep")
    bloque("la plantilla JSON", "wc -l plantilla.json", "wc -l plantilla.json")
    bloque("decompilarla", "az bicep decompile --file plantilla.json; cat plantilla.bicep",
           "az bicep decompile --file plantilla.json >/dev/null 2>&1; cat plantilla.bicep; wc -l plantilla.bicep")

    OUT.append("## 3 · Un blob privado y un SAS de solo lectura (Azurite)\n")
    ex(f"az storage container create -n fotos --connection-string '{CONN}' -o none && echo 'hola desde azurite' > foto.txt && "
       f"az storage blob upload -c fotos -n foto.txt -f foto.txt --connection-string '{CONN}' --only-show-errors -o none")
    bloque("leerlo sin permiso", f"curl -s -o /dev/null -w '%{{http_code}}' {URL}",
           f"curl -s -o /dev/null -w '%{{http_code}}\\n' {URL}")
    caduca = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%MZ")
    sas, _ = ex(f"az storage blob generate-sas -c fotos -n foto.txt --permissions r --expiry {caduca} "
                f"--connection-string '{CONN}' -o tsv")
    ex(f"echo '{sas}' > sas.txt")
    bloque("el SAS: solo lectura, caduca en una hora", "az storage blob generate-sas --permissions r --expiry …",
           "tr '&' '\\n' < sas.txt | grep -E '^(se|sp|sv|sr)=' ; echo \"sig=$(grep -o 'sig=[^&]*' sas.txt | cut -c5-12)…\"")
    bloque("leerlo con el SAS", f"curl -s \"{URL}?$SAS\"", f"curl -s \"{URL}?$(cat sas.txt)\"")
    bloque("intentar escribir con el mismo SAS", f"curl -s -X PUT -H 'x-ms-blob-type: BlockBlob' -d otro \"{URL}?$SAS\"",
           f"curl -s -o /dev/null -w '%{{http_code}}\\n' -X PUT -H 'x-ms-blob-type: BlockBlob' -d otro \"{URL}?$(cat sas.txt)\"; "
           f"curl -s \"{URL}?$(cat sas.txt)\"")

    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
