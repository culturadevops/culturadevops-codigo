# SALIDA — uv contra pip con un requirements de verdad, medidos en esta máquina

> Corrida del 2026-08-31 06:57. Regenerable con
> `python investigacion/pruebas_uv_pip.py`. ⛔ Ninguna cifra de blog.
> `requirements-datos.txt`: 15 paquetes directos de un proyecto de datos típico
> (pandas, numpy, scikit-learn, matplotlib, boto3…) → **49 paquetes reales**
> instalados, venv de **524 MB**. Docker, reloj del contenedor.

| medición | pip | uv | ratio |
|---|---|---|---|
| instalación fría (mediana de 3) | **21.2 s** | **8.6 s** | 2.5x |
| con la caché del gestor caliente | 13.1 s | 0.2 s | 52.8x |

Corridas frías completas: pip [22.0, 21.2, 21.1] s · uv [8.6, 8.3, 9.6] s

Contexto del 153 (ya medido): con DOS dependencias puras, uv no cambia nada
(frío 7,1 s contra 3,1 por bajar su builder). Esta es la otra mitad de esa historia.