# -*- coding: utf-8 -*-
"""10 tips para Amazon VPC — demos ejecutables con la AWS CLI contra moto. Escribe SALIDA.md.

⚠️ moto emula la API de EC2/VPC, no mueve paquetes ni factura: lo que se enseña es la
   configuración que devuelve la API.

    python correr.py
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

with Banco(AQUI, "10 tips para Amazon VPC", puerto=5104) as b:
    b.titulo("Una VPC y sus subredes")
    vpc = b.aws("ec2", "create-vpc", "--cidr-block", "10.0.0.0/16", "--query", "Vpc.VpcId",
                "--output", "text")
    b.aws("ec2", "create-subnet", "--vpc-id", vpc, "--cidr-block", "10.0.1.0/24",
          "--availability-zone", "us-east-1a", "--query", "Subnet.CidrBlock",
          mostrar="ec2 create-subnet --vpc-id <vpc> --cidr-block 10.0.1.0/24 --availability-zone us-east-1a")
    b.aws("ec2", "create-subnet", "--vpc-id", vpc, "--cidr-block", "10.0.1.128/25",
          "--availability-zone", "us-east-1a", "--query", "Subnet.CidrBlock",
          mostrar="ec2 create-subnet --vpc-id <vpc> --cidr-block 10.0.1.128/25 --availability-zone us-east-1a")
    b.aws("ec2", "create-vpc", "--cidr-block", "10.0.0.0/8", "--query", "Vpc.VpcId",
          mostrar="ec2 create-vpc --cidr-block 10.0.0.0/8")

    b.titulo("Cinco direcciones reservadas por subred")
    b.aws("ec2", "create-subnet", "--vpc-id", vpc, "--cidr-block", "10.0.9.0/28",
          "--availability-zone", "us-east-1b",
          "--query", "Subnet.{Cidr:CidrBlock,IPsLibres:AvailableIpAddressCount}",
          mostrar="ec2 create-subnet --vpc-id <vpc> --cidr-block 10.0.9.0/28 --availability-zone us-east-1b")

    b.titulo("Una IPv4 pública sin usar")
    b.aws("ec2", "allocate-address", "--domain", "vpc", "--query", "AllocationId", "--output",
          "text", guardar=False)
    b.aws("ec2", "describe-addresses",
          "--query", "Addresses[0].{Asignada:AllocationId,Asociada:AssociationId}")

    b.titulo("Endpoint de gateway para S3")
    rt = b.aws("ec2", "describe-route-tables", "--filters", f"Name=vpc-id,Values={vpc}",
               "--query", "RouteTables[0].RouteTableId", "--output", "text", guardar=False)
    b.aws("ec2", "create-vpc-endpoint", "--vpc-id", vpc, "--vpc-endpoint-type", "Gateway",
          "--service-name", "com.amazonaws.us-east-1.s3", "--route-table-ids", rt,
          "--query", "VpcEndpoint.{Tipo:VpcEndpointType,Servicio:ServiceName,Estado:State}",
          mostrar="ec2 create-vpc-endpoint --vpc-id <vpc> --vpc-endpoint-type Gateway "
                  "--service-name com.amazonaws.us-east-1.s3 --route-table-ids <tabla>")
    b.aws("ec2", "describe-route-tables", "--route-table-ids", rt,
          "--query", "RouteTables[0].Routes[].{Destino:DestinationCidrBlock || DestinationPrefixListId,"
                     "Via:GatewayId}",
          mostrar="ec2 describe-route-tables --route-table-ids <tabla>")

    # Grupo de seguridad por defecto: moto 5.2.3 lo crea SIN la regla de entrada desde el propio
    # grupo que pone AWS. Miente: ese tip va solo con la documentación.

    b.titulo("Flow Logs")
    b.aws("ec2", "create-flow-logs", "--resource-type", "VPC", "--resource-ids", vpc,
          "--traffic-type", "REJECT", "--log-destination-type", "cloud-watch-logs",
          "--log-group-name", "/vpc/rechazos",
          "--deliver-logs-permission-arn", "arn:aws:iam::123456789012:role/flow-logs",
          "--query", "length(FlowLogIds)",
          mostrar="ec2 create-flow-logs --resource-type VPC --resource-ids <vpc> "
                  "--traffic-type REJECT --log-destination-type cloud-watch-logs "
                  "--log-group-name /vpc/rechazos ...")
    b.aws("ec2", "describe-flow-logs",
          "--query", "FlowLogs[0].{Trafico:TrafficType,Destino:LogGroupName}")
