# -*- coding: utf-8 -*-
"""10 tips para AWS Organizations y las SCP — demos con la AWS CLI contra moto. Escribe SALIDA.md.

⚠️ moto emula la API de Organizations, NO evalúa las SCP al hacer llamadas: lo que se enseña es la
   estructura (raíz, OU, políticas adjuntas) y las restricciones de la propia API.

    python correr.py
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

NO_SALIR = {"Version": "2012-10-17", "Statement": [{
    "Sid": "NoSalirNiCerrar", "Effect": "Deny",
    "Action": ["organizations:LeaveOrganization", "account:CloseAccount"], "Resource": "*"}]}

with Banco(AQUI, "10 tips para AWS Organizations", puerto=5102) as b:
    b.titulo("Una organización creada por la CLI")
    b.aws("organizations", "create-organization", "--feature-set", "ALL",
          "--query", "Organization.FeatureSet")
    raiz = b.aws("organizations", "list-roots", "--query", "Roots[0].Id", "--output", "text",
                 guardar=False)
    b.aws("organizations", "enable-policy-type", "--root-id", raiz,
          "--policy-type", "SERVICE_CONTROL_POLICY", "--query", "Root.PolicyTypes",
          mostrar="organizations enable-policy-type --root-id <raíz> --policy-type SERVICE_CONTROL_POLICY")
    b.aws("organizations", "list-policies-for-target", "--target-id", raiz,
          "--filter", "SERVICE_CONTROL_POLICY", "--query", "Policies[].Name",
          mostrar="organizations list-policies-for-target --target-id <raíz> --filter SERVICE_CONTROL_POLICY")

    b.titulo("Una OU de pruebas y una cuenta dentro")
    ou = b.aws("organizations", "create-organizational-unit", "--parent-id", raiz,
               "--name", "pruebas-scp", "--query", "OrganizationalUnit.Id", "--output", "text",
               mostrar="organizations create-organizational-unit --parent-id <raíz> --name pruebas-scp")
    cuenta = b.aws("organizations", "create-account", "--email", "dev@example.com",
                   "--account-name", "dev", "--query", "CreateAccountStatus.AccountId",
                   "--output", "text")
    b.aws("organizations", "move-account", "--account-id", cuenta, "--source-parent-id", raiz,
          "--destination-parent-id", ou,
          mostrar="organizations move-account --account-id <dev> --source-parent-id <raíz> "
                  "--destination-parent-id <pruebas-scp>")

    b.titulo("La SCP que impide salir o cerrar la cuenta")
    (AQUI / "no-salir.json").write_text(json.dumps(NO_SALIR, indent=2), encoding="utf-8")
    b.anotar("cat no-salir.json", (AQUI / "no-salir.json").read_text(encoding="utf-8"))
    pol = b.aws("organizations", "create-policy", "--name", "no-salir-ni-cerrar",
                "--type", "SERVICE_CONTROL_POLICY", "--description", "Deny Leave y CloseAccount",
                "--content", "file://no-salir.json", "--query", "Policy.PolicySummary.Id",
                "--output", "text")
    b.aws("organizations", "attach-policy", "--policy-id", pol, "--target-id", ou,
          mostrar="organizations attach-policy --policy-id <no-salir-ni-cerrar> --target-id <pruebas-scp>")
    b.aws("organizations", "list-policies-for-target", "--target-id", ou,
          "--filter", "SERVICE_CONTROL_POLICY", "--query", "Policies[].Name",
          mostrar="organizations list-policies-for-target --target-id <pruebas-scp> --filter SERVICE_CONTROL_POLICY")

    # Quitar FullAWSAccess: moto 5.2.3 deja quitar la ÚLTIMA SCP de una cuenta, y AWS no (límite
    # duro: «You can't remove the last SCP from an entity»). Miente: no se enseña.

    b.titulo("El tamaño cuenta los espacios")
    bonito = json.dumps(NO_SALIR, indent=2)
    compacto = json.dumps(NO_SALIR, separators=(",", ":"))
    b.anotar("python: len(no-salir.json con sangría) · len(el mismo JSON compacto)",
             f"con sangría: {len(bonito)} caracteres\ncompacto:    {len(compacto)} caracteres")
