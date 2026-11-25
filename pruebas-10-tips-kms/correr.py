# -*- coding: utf-8 -*-
"""10 tips para AWS KMS — demos ejecutables con la AWS CLI contra moto. Escribe SALIDA.md.

    python correr.py
"""
import base64
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

with Banco(AQUI, "10 tips para AWS KMS", puerto=5103) as b:
    b.titulo("Una clave creada solo con lo obligatorio")
    clave = b.aws("kms", "create-key", "--description", "datos-de-pagos",
                  "--query", "KeyMetadata.KeyId", "--output", "text")
    b.aws("kms", "get-key-policy", "--key-id", clave, "--policy-name", "default",
          "--query", "Policy", "--output", "text", mostrar="kms get-key-policy --key-id <clave> --policy-name default")
    b.aws("kms", "get-key-rotation-status", "--key-id", clave,
          mostrar="kms get-key-rotation-status --key-id <clave>")

    b.titulo("Rotación automática")
    b.aws("kms", "enable-key-rotation", "--key-id", clave, "--rotation-period-in-days", "30",
          mostrar="kms enable-key-rotation --key-id <clave> --rotation-period-in-days 30")
    b.aws("kms", "enable-key-rotation", "--key-id", clave, "--rotation-period-in-days", "180",
          mostrar="kms enable-key-rotation --key-id <clave> --rotation-period-in-days 180")
    b.aws("kms", "get-key-rotation-status", "--key-id", clave,
          mostrar="kms get-key-rotation-status --key-id <clave>")

    b.titulo("Un alias, y cifrar con él")
    b.aws("kms", "create-alias", "--alias-name", "alias/pagos", "--target-key-id", clave,
          mostrar="kms create-alias --alias-name alias/pagos --target-key-id <clave>")
    (AQUI / "secreto.txt").write_text("numero-de-tarjeta-de-prueba", encoding="utf-8")
    cifrado = b.aws("kms", "encrypt", "--key-id", "alias/pagos", "--plaintext", "fileb://secreto.txt",
                    "--query", "CiphertextBlob", "--output", "text")
    (AQUI / "cifrado.bin").write_bytes(base64.b64decode(cifrado))

    b.titulo("Rotar no cambia la clave ni rompe lo cifrado")
    b.aws("kms", "rotate-key-on-demand", "--key-id", clave,
          mostrar="kms rotate-key-on-demand --key-id <clave>")
    b.aws("kms", "describe-key", "--key-id", "alias/pagos", "--query", "KeyMetadata.KeyId",
          "--output", "text", mostrar="kms describe-key --key-id alias/pagos  # ¿el mismo id?")
    plano = b.aws("kms", "decrypt", "--ciphertext-blob", "fileb://cifrado.bin",
                  "--query", "Plaintext", "--output", "text", guardar=False)
    b.anotar("aws kms decrypt --ciphertext-blob fileb://cifrado.bin  # cifrado ANTES de rotar",
             base64.b64decode(plano).decode("utf-8"))

    b.titulo("Programar el borrado")
    # moto 5.2.3 MIENTE aquí y no se enseña: acepta una espera de 3 días (AWS exige 7-30) y deja
    # cifrar con una clave pendiente de borrado (AWS no deja usarla).
    b.aws("kms", "schedule-key-deletion", "--key-id", clave, "--pending-window-in-days", "7",
          "--query", "KeyId", "--output", "text", guardar=False)
    b.aws("kms", "describe-key", "--key-id", clave, "--query", "KeyMetadata.KeyState",
          mostrar="kms schedule-key-deletion --key-id <clave> --pending-window-in-days 7 "
                  "&& aws kms describe-key ...KeyState")
    b.aws("kms", "cancel-key-deletion", "--key-id", clave, "--query", "KeyId", "--output", "text",
          guardar=False)
    b.aws("kms", "describe-key", "--key-id", clave, "--query", "KeyMetadata.KeyState",
          mostrar="kms cancel-key-deletion --key-id <clave> && aws kms describe-key ...KeyState")
