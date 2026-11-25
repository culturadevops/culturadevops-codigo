# 🚀 Python para automatizar despliegues — material del curso

Código del vídeo [«Python para automatizar despliegues (curso para administradores)»](https://youtu.be/iQOUNfyivfI) del canal Cultura DevOps.

> **El vídeo de este código está disponible para los miembros del canal: https://youtu.be/iQOUNfyivfI**

---

> 🎬 Acompaña al vídeo **«Python para automatizar despliegues (curso para administradores)»** del canal **Cultura DevOps** (solo miembros).

Código del curso **«Python para automatizar despliegues»** de
[Cultura DevOps](https://www.youtube.com/@culturadevops), exclusivo para miembros del canal.

> **Un script de despliegue no falla cuando lo escribes. Falla la segunda vez que corre**, a
> mitad de un corte, con el servicio lento o con otro despliegue lanzado a la vez. Cada lección
> reproduce uno de esos fallos en tu máquina y enseña cómo se escribe para que no pase.

Si vienes del curso **«Python básico para administradores de sistemas»**, esto es lo siguiente:
ya sabes el lenguaje; aquí se trata de que el script no te deje la producción a medias.

## Cómo usar esto

```bash
git clone <este-repo> && cd curso-python-despliegues
python --version          # hace falta 3.10 o superior
python ejecutar_todo.py   # corre las 12 lecciones y regenera SALIDA.md
```

**Cero dependencias y nada fuera de tu máquina.** Los servidores lentos, colgados o que
arrancan a medias los levanta cada lección en `127.0.0.1`, y todo se escribe en carpetas
temporales que se borran al acabar.

## Las 12 lecciones

| # | directorio | la trampa | lo que hay que hacer |
|---:|---|---|---|
| 1 | `01_subprocess` | `run()` sin `check=True`: el comando falla y el script sigue | `check=True`, lista de argumentos, `timeout`, guardar stderr |
| 2 | `02_dry_run` | el dry-run sale antes de calcular nada y no simula | un plan que se calcula igual en los dos modos |
| 3 | `03_idempotencia` | añadir una línea dos veces la deja dos veces | «que quede así», y decir cambiado / sin cambios |
| 4 | `04_atomico` | escribir encima: si se corta, no queda ni la vieja ni la nueva | temporal al lado y `os.replace` |
| 5 | `05_reintentos` | reintentarlo todo, o algo que no es idempotente | solo lo transitorio, espera exponencial con azar, clave de idempotencia |
| 6 | `06_timeouts` | sin timeout se espera para siempre; y el timeout no es total | `timeout=` siempre, y un plazo total aparte |
| 7 | `07_salud` | «el puerto contesta» o «da 200»... de la versión vieja | esperar a que conteste TU versión, con plazo |
| 8 | `08_marcha_atras` | desplegar encima, limpiar de más, migrar la base sin vuelta | una carpeta por release, un puntero, ampliar antes de romper |
| 9 | `09_cerrojo` | dos despliegues a la vez; el cerrojo huérfano | `os.O_EXCL` y caducidad |
| 10 | `10_secretos` | variable vacía que cambia la ruta; el secreto en el log | pedirlas todas, tapar el secreto, `repr=False` |
| 11 | `11_salida` | capturar el error y salir con 0; logs mezclados con el resultado | códigos que significan algo, logs a stderr |
| 12 | `12_proyecto` | — | `desplegar.py`: todo lo anterior en un script, probado con 8 casos |

`12_proyecto/desplegar.py` es un script de verdad: úsalo de base para el tuyo.

## La regla de la casa

Todo lo que se ve en el vídeo está **ejecutado**, no copiado. `SALIDA.md` es la salida literal
de `ejecutar_todo.py` en la máquina donde se grabó, con su versión de Python y su fecha. Los
tiempos y los pid cambian en cada ejecución; lo demás tiene que coincidir. Si algo no coincide
en la tuya, es un dato, no un fallo: dilo en los comentarios.

## Licencia

El código es para que lo copies, lo rompas y lo uses en tu trabajo. Los vídeos son del canal.

---

<!-- ficha-repos-miembros -->
## Ficha rápida

### Requisitos

- Python 3.10 o superior. Cero dependencias.

### Cómo ejecutarlo

```bash
git clone <este-repo> && cd curso-python-despliegues
python ejecutar_todo.py
```

El detalle de cada lección está arriba, en este mismo README.

### Estructura de carpetas

```
curso-python-despliegues/
├── 01_subprocess/
│   └── ejecutar_comandos.py
├── 02_dry_run/
│   └── simulacro.py
├── 03_idempotencia/
│   └── dos_veces.py
├── 04_atomico/
│   └── escribir_sin_romper.py
├── 05_reintentos/
│   └── reintentar_bien.py
├── 06_timeouts/
│   └── sin_limite.py
├── 07_salud/
│   └── comprobar_salud.py
├── 08_marcha_atras/
│   └── volver_atras.py
├── 09_cerrojo/
│   └── uno_a_la_vez.py
├── 10_secretos/
│   └── config_y_secretos.py
├── 11_salida/
│   └── codigos_de_salida.py
├── 12_proyecto/
│   ├── desplegar.py
│   └── escenario.py
├── .gitignore
├── ejecutar_todo.py
├── README.md
└── SALIDA.md
```
