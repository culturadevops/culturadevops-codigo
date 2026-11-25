$ python --version
Python 3.11.9
$ cat precios.py
import sys


def con_impuesto(precio: int) -> float:
    return precio * 118 / 100


def main() -> None:
    total = 0
    precio = sys.argv[1]
    print("con impuesto:", con_impuesto(precio))


main()

$ python precios.py 100
    return precio * 118 / 100
           ~~~~~~~~~~~~~^~~~~
TypeError: unsupported operand type(s) for /: 'str' and 'int'
(código de salida: 1)

$ ruff check precios.py
F841 Local variable `total` is assigned to but never used
  --> precios.py:9:5
   |
 8 | def main() -> None:
 9 |     total = 0
   |     ^^^^^
10 |     precio = sys.argv[1]
11 |     print("con impuesto:", con_impuesto(precio))
   |
help: Remove assignment to unused variable `total`
Found 1 error.
No fixes available (1 hidden fix can be enabled with the `--unsafe-fixes` option).

$ mypy precios.py
precios.py:11: error: Argument 1 to "con_impuesto" has incompatible type "str"; expected "int"  [arg-type]
Found 1 error in 1 file (checked 1 source file)

$ # arreglo: int(sys.argv[1]) y fuera la variable sin usar
$ ruff check precios.py && mypy precios.py && python precios.py 100
All checks passed!
Success: no issues found in 1 source file
con impuesto: 118.0

$ head -4 resumen.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich==14.2.0"]
# ///
$ uv run resumen.py
script con sus dependencias dentro: listo
$ ruff --version && mypy --version && uv --version
ruff 0.14.0
mypy 1.18.2 (compiled: yes)
uv 0.9.2 (141369ce7 2025-10-10)
