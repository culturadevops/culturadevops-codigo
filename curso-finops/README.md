# 💸 La factura: FinOps para el que paga de su bolsillo — material del curso

Código del vídeo [«La factura de AWS: FinOps para el que paga de su bolsillo (curso completo)»](https://youtu.be/v59Pm6lQ6HM) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/v59Pm6lQ6HM**

---

> 🎬 Acompaña al vídeo **«La factura de AWS: FinOps para el que paga de su bolsillo (curso completo)»** del canal **Cultura DevOps** (solo miembros).

Código del curso de [Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros
del canal.

> Desde julio de 2025, una cuenta nueva de AWS no tiene un año gratis: tiene créditos (100 USD al
> abrirla y otros 100 por usar servicios) y un plan que dura seis meses o hasta gastarlos. Este curso
> es lo que hay que saber para que esos créditos no se los coma un NAT gateway olvidado.

⚠️ **Sin cuenta y sin factura real.** Todo corre contra [moto](https://github.com/getmoto/moto) (un
emulador de AWS) y los importes son **precio de lista × uso**, con la lista de precios pública de AWS
(`precios/`, con su fecha). Las citas de la documentación están en `FUENTES.md`.

## Cómo usar esto

```bash
pip install boto3 "moto[server]"     # y OpenTofu para la lección 6
python ejecutar_todo.py              # las 6 lecciones y SALIDA.md
python cazador.py --endpoint http://127.0.0.1:5000   # contra moto en modo servidor
python cazador.py                    # contra tu cuenta de verdad (solo lee)
```

## Las 6 lecciones

| # | script | lo que enseña |
|---:|---|---|
| 1 | `l01_plan_gratuito.py` | el plan gratuito de 2025, y cuánto duran 200 USD con lo que se suele dejar encendido |
| 2 | `l02_presupuesto.py` | un presupuesto con avisos real y previsto, por API; se actualiza hasta 3 veces al día y no para nada |
| 3 | `l03_etiquetas.py` | el coste por proyecto, y lo que no tiene dueño; las etiquetas hay que activarlas |
| 4 | `l04_lo_que_sigue_cobrando.py` | borrar la instancia no borra el disco, la instantánea, la IP ni el NAT |
| 5 | `l05_hora_o_peticion.py` | t3.micro contra Lambda: el punto de corte, en peticiones al mes |
| 6 | `l06_destruir.py` | `tofu destroy` borra lo suyo; lo hecho a mano se queda, y `default_tags` lo delata |

## El proyecto: cazador.py

Recorre una región y apunta lo que cobra por estar: instancias, su IPv4 pública, discos (sueltos o
no), instantáneas que no respaldan ninguna imagen, IPs fijas y NAT gateways. Pone precio mensual a
cada cosa y sale con 1 si encuentra algo. Solo lee: se puede programar a diario contra la cuenta real.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Python 3.10 o superior con `boto3` y `moto` (para el emulador).
- Opcional: una cuenta de AWS propia para `cazador.py` (solo lee).

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-finops
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-finops/
├── infra/
│   └── main.tf
├── lecciones/
│   ├── l01_plan_gratuito.py
│   ├── l02_presupuesto.py
│   ├── l03_etiquetas.py
│   ├── l04_lo_que_sigue_cobrando.py
│   ├── l05_hora_o_peticion.py
│   └── l06_destruir.py
├── precios/
│   ├── AmazonVPC-us-east-1.json
│   ├── AWSLambda-us-east-1.json
│   └── ec2-us-east-1.json
├── .gitattributes
├── .gitignore
├── cazador.py
├── ejecutar_todo.py
├── FUENTES.md
├── precios.py
├── README.md
└── SALIDA.md
```
