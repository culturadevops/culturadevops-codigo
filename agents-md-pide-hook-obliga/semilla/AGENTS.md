# inventario-tools

Herramientas internas del equipo de plataforma: utilidades de cálculo en Go, un
módulo de inventario en Python y el script de respaldo en Bash.

## Estructura

- `go/`: módulo `demo` (Go 1.26). Funciones puras, sin dependencias externas.
- `py/`: `inventario.py`, solo biblioteca estándar (Python 3.11).
- `sh/`: scripts de operación. Se ejecutan con `bash`, no con `sh`.

## Estilo

- Nombres en español, como el resto del código.
- Funciones cortas; si una pasa de 40 líneas, pártela.
- Comentarios solo donde el código no se explique solo.
- Go: los errores se devuelven, no se usa `panic`.
- Python: anotaciones de tipo en las funciones públicas.
- Bash: `set -euo pipefail` al principio de cada script.

## Antes de terminar una tarea

Pasa el verificador de cada archivo que tocaste y deja cero avisos:

- Go: `gofmt -l go/` no debe listar nada, y `go vet ./...` desde `go/` sin avisos.
- Python: `ruff check <archivo>` sin avisos.
- Bash: `shellcheck <archivo>` sin avisos.

No desactives avisos (nada de `# noqa`, `# shellcheck disable` ni `//nolint`):
corrige el código.

## Commits

- No hagas commits: el equipo revisa el diff a mano.
- No toques archivos fuera de la carpeta de la tarea.
