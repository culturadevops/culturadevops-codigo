# Tests contra LocalStack en vez de mocks: la prueba que sí demuestra algo — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. almacen.py · lo que vamos a probar

```console
class Almacen:
    def guardar(self, anio, numero, contenido):
        self.s3.put_object(
            Bucket=self.cubo,
            Key="%s/%s.txt" % (anio, numero),
            Body=contenido)

    def listar(self, anio):
        # recorre paginando
```

## 2. la prueba con simulacro

```console
def test_guardar_con_simulacro():
    s3 = MagicMock()
    a = Almacen(s3, "facturas")
    a.guardar("2026", "001", b"hola")
    s3.put_object.assert_called_once()
```

## 3. la prueba que no debería pasar

```console
def test_cubo_que_no_existe():
    s3 = MagicMock()
    a = Almacen(s3,
        "cubo-que-no-existe-jamas")
    a.guardar("2026", "001", b"hola")

# ni un assert que falle
```

## 4. las dos pruebas

```console
$ pytest -q test_con_simulacro.py

  el simulacro dice que si a todo
  guardado en un cubo inexistente...
  y la prueba pasa

2 passed in 0.02s
```

## 5. conftest.py · el cliente

```console
import boto3, pytest

@pytest.fixture
def s3():
    return boto3.Session(
        profile_name="lab").client("s3")
```

## 6. conftest.py · el escenario limpio

```console
@pytest.fixture
def cubo(s3):
    nombre = "pruebas-facturas"
    crear_si_no_existe(s3, nombre)
    vaciar(s3, nombre)   # paginando
    return nombre
```

## 7. una prueba que comprueba el comportamiento

```console
def test_guardar_y_listar(s3, cubo):
    a = Almacen(s3, cubo)
    a.guardar("2026", "001", b"hola")
    a.guardar("2026", "002", b"adios")
    a.guardar("2025", "099", b"viejo")

    assert a.listar("2026") == [
        "2026/001.txt", "2026/002.txt"]
```

## 8. ahora sí exige el fallo

```console
def test_cubo_que_no_existe(s3):
    a = Almacen(s3,
        "cubo-que-no-existe-jamas")
    with pytest.raises(ClientError):
        a.guardar("2026", "001", b"hola")
```

## 9. la prueba que caza el fallo de la paginación

```console
def test_lista_mas_de_mil(s3, cubo):
    a = Almacen(s3, cubo)
    for i in range(1200):
        a.guardar("2026", "%04d" % i, b"x")

    assert len(a.listar("2026")) == 1200
```

## 10. las tres, contra el laboratorio

```console
$ pytest -q test_contra_lab.py

...                          [100%]

3 passed in 3.07s
```
