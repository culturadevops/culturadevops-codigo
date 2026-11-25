# ⚠️ CÓDIGO VULNERABLE A PROPÓSITO — SOLO PARA LA DEMO

Esta carpeta tiene la MISMA aplicación mínima escrita en cinco lenguajes (PHP, Python, Go, Java y Node), con vulnerabilidades
puestas a propósito para medir qué detecta cada escáner. **Nunca se despliega ni se expone en ninguna red**: solo la leen los
analizadores, dentro de contenedores.

Vídeos de cultura-devops que la usan: «Un escáner de seguridad para cada lenguaje en tu pipeline» y «Semgrep vs CodeQL vs SonarQube».

## La verdad de referencia (igual en los cinco lenguajes)

| Caso | Dónde | ¿Es real? |
|---|---|---|
| V1 | `usuario`: el parámetro `id` se pega dentro del SQL | **Sí**: inyección SQL |
| V2 | `ping`: el parámetro `host` se pega dentro de un comando del sistema | **Sí**: inyección de comandos |
| V3 | `buscar`: el parámetro `q` pasa por una función de OTRO archivo que arma el SQL | **Sí**: inyección SQL entre archivos |
| S1 | `usuario_seguro`: la misma consulta, con parámetros (`?`) | No: está bien hecho |
| S2 | `pedido`: el `id` se convierte a número entero antes de pegarlo | No: un entero no puede inyectar nada |

Además, cada lenguaje declara **una dependencia vieja con vulnerabilidades conocidas**, para los analizadores de dependencias (SCA).

`correr.py` lo ejecuta todo y escribe `SALIDA.md`.
