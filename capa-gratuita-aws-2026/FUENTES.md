# Fuentes — vídeos 692 (capa gratuita 2026) y 693 (qué es AWS 2026), cultura-devops

Consultadas el **2026-10-29**. Citas literales; lo que no está aquí ni en SALIDA.md no se afirma en el vídeo.

## Plan gratuito nuevo (cuentas abiertas el 15-07-2025 o después)

**Anuncio** («Posted on: Jul 16, 2025»)
https://aws.amazon.com/about-aws/whats-new/2025/07/aws-free-tier-credits-month-free-plan/
- «new customers receive $100 in AWS credits upon sign-up and can earn an additional $100 in credits by using services such as Amazon EC2 and Amazon Bedrock»
- «The free account plan expires either 6 months after sign-up or when Free Tier credits are depleted, whichever comes first»
- «customers continue to have access to over 30 always-free services»

**AWS News Blog** (15-jul-2025)
https://aws.amazon.com/blogs/aws/aws-free-tier-update-new-customers-can-get-started-and-explore-aws-with-up-to-200-in-credits/
- «If your AWS account was created before July 15, 2025, you'll continue to be in the legacy Free Tier program.»
- «You can also earn an additional $20 credits for each of these five AWS service activities you complete.» (EC2, RDS, Lambda con function URL, Bedrock playground, AWS Budgets)
- «The free account plan ensures you won't incur any charges until you upgrade to a paid plan.»
- «You'll have 90 days to reopen your account by upgrading to a paid plan.»

**Guía de facturación** · https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html
- «If you are new to AWS, you receive USD $100 in credits after you create an account, regardless of your account plan.»
- «free account plans don't have access to certain AWS services that would rapidly consume the entire AWS Free Tier credit amount, or hardware purchases.»
- «When you usage exceeds your credit balance or when you use a service where credits don't apply, you pay standard pay-as-you-go pricing.» (plan de pago)
- «If you go beyond these monthly allowances, your AWS Free Tier credits are automatically applied to cover the eligible costs.»

**Actividades** · https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans-activities.html
- EC2, Bedrock, Lambda y RDS: «This activity incurs AWS service charges that are deducted from your AWS Free Tier credits.» (Budgets no lleva esa nota)

**FAQ** · https://aws.amazon.com/free/free-tier-faqs/
- «No, you cannot extend your Free plan beyond 6 months.»
- «Once your credits are exhausted, you will need to upgrade to a Paid plan to continue using your account»
- «AWS will retain your data for 90 days after your Free plan expires.»
- «If you don’t upgrade your account within 90 days, AWS will permanently erase your AWS account and all its content.»
- «No, you cannot downgrade your Paid plan to the Free plan.»
- «The credits you earned from completing activities expire 12 months from the date you create your AWS account.»
- ⚠️ La FAQ se contradice sobre la caducidad de los créditos de alta (6 meses en una respuesta, 12 en otra tras pasar a pago): en el vídeo no se da esa cifra.

## Capa gratuita vieja (cuentas abiertas antes del 15-07-2025)

**Guía de EC2** · https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html
- Tabla «before / on or after July 15, 2025»: tipos elegibles `t2.micro`, `t3.micro` (antes) frente a `t3.micro`, `t3.small`, `t4g.micro`, `t4g.small`, `c7i-flex.large`, `m7i-flex.large` (después).
- Antes: «Your Free Tier lasts for 12 months from the date you create your account. During this time, if you exceed your Free Tier usage limits, you are billed pay-as-you-go rates.»
- Después: «Your Free Tier lasts for 6 months from the date you created your account, or when your credits are used up, whichever happens first. You can't exceed your Free Tier limits.»

**FAQ heredada** · https://aws.amazon.com/free/legacy/free-tier-faqs
- «you will receive 750 Amazon EC2 Linux Micro Instance hours for free across all of the regions you use»
- «for one year from the date the account was activated» · después: «you simply pay standard, pay-as-you-go service rates»
- Cuenta del canal: la última cuenta posible del sistema viejo se abrió el 14-07-2025, así que sus 12 meses terminaron el 14-07-2026. En octubre de 2026 ninguna cuenta conserva los 12 meses.

## Precios y gratuidades permanentes
- Lista de precios pública, sin cuenta: `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<Oferta>/current/<región>/index.csv` (lista.py guarda el filtro y la fecha de publicación de cada una en `precios/`).
- Siempre gratis, en la propia lista: «$0 for 100GB of data transfer out to the internet, aggregated globally, each month» (AWSDataTransfer) · «AWS Lambda - Requests Free Tier - 1,000,000 Requests» y «AWS Lambda - Compute Free Tier - 400,000 GB-Seconds» (AWSLambda).
- Guía de VPC, precios · https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html#pricing — «There's no additional charge for using a VPC.» · «If you are an existing or new AWS Free Tier customer, you get 750 hours of public IPv4 address usage with the EC2 service at no charge.» (el cálculo descuenta esas 750 h del total de IPv4, en el caso más favorable).
- IAM · https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html — «AWS Identity and Access Management (IAM), AWS IAM Identity Center and AWS Security Token Service (AWS STS) are features of your AWS account offered at no additional charge.»
- EC2 bajo demanda · https://aws.amazon.com/ec2/pricing/on-demand/ — «Each partial instance-hour consumed will be billed per-second for Linux» · «(minimum of 60 seconds)».
- VPC · https://aws.amazon.com/vpc/pricing/ — «a charge of $0.045 per hour will always apply once the NAT gateway is provisioned and available» (ejemplo de la página).
- AWS Budgets · https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html — «AWS Budgets information is updated up to three times a day.» (cita del curso FinOps, comprobada el 2026-10-05).

## Parar una máquina (693)
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-ec2-instance-stop-start-works.html
- «You are not charged for usage or data transfer fees for a stopped instance. Charges are incurred to store Amazon EBS storage volumes.»
- «Each time you start a stopped instance, you are charged for a minimum of one minute of usage. After one minute, you are charged for only the seconds you use.»
- Al parar se pierde «The public IPv4 address that Amazon EC2 automatically assigned to the instance»; las Elastic IP asociadas se siguen cobrando.

## Infraestructura global (693)
https://aws.amazon.com/about-aws/global-infrastructure/
- 39 regiones geográficas y 124 zonas de disponibilidad; anunciadas 2 regiones más (Arabia Saudita y Chile).
- «each AWS Region consisting of at least three independent, physically separate Availability Zones (AZs)»
- La lista de precios de EC2 (`region_index.json`) trae 36 regiones con nombre de región (34 comerciales + 2 GovCloud), más zonas locales y Wavelength: SALIDA del 693.

## Sin cuenta real
No hay cuenta de AWS en este banco: las demos van contra moto 5.2.3 (emula la API, no la factura) y todo importe es **precio de lista × uso**.
