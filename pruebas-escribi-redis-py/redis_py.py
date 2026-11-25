# -*- coding: utf-8 -*-
"""redis_py.py — un servidor Redis escrito en Python, para el video 219 de cultura-devops.

LA PROMESA DEL VIDEO, que este fichero tiene que cumplir: que el `redis-cli` OFICIAL se conecte
a esto y funcione sin notar la diferencia. Por eso habla RESP de verdad y contesta a COMMAND,
que es lo primero que manda redis-cli al conectarse (si no, se queda colgado).

QUE SE APRENDE ESCRIBIENDOLO, que es el angulo del video:
  1. RESP es texto plano y cabe en una servilleta.
  2. Un diccionario NO es un Redis: falta la EXPIRACION, y ahi esta el diseno de verdad.
  3. Un solo hilo te regala la atomicidad: sin candados, sin carreras, sin interbloqueos.

LO QUE NO HACE, y en el video se dice claro: no hay persistencia (RDB/AOF), ni replicacion, ni
cluster, ni transacciones, ni pub/sub. Eso es lo que hace que Redis sea Redis.

Sin dependencias: solo la biblioteca estandar.

    python redis_py.py --puerto 6380
"""
import argparse
import socket
import socketserver
import threading
import time

# ───────────────────────────────────────────────────────────── el almacen ──

# valor -> (dato, instante_de_caducidad o None)
#
# Se guarda el INSTANTE, no la duracion: si guardas la duracion tienes que ir restando, y eso es
# un bucle que toca todas las claves en cada vuelta.
DATOS = {}

# Un solo candado para todo el almacen. En un Redis de verdad no hace falta porque solo hay un
# hilo; aqui el servidor atiende cada cliente en su hilo, asi que el candado es lo que reproduce
# esa garantia. Es la traduccion honesta de "un solo hilo" a Python.
CANDADO = threading.Lock()


def vivo(k):
    """¿Sigue valida la clave? Y BORRA la caducada de paso.

    Esto es el "borrado perezoso" de Redis: no hay ningun proceso mirando el reloj de cada clave;
    la clave muerta se descubre cuando alguien la pide.
    """
    v = DATOS.get(k)
    if v is None:
        return None
    dato, caduca = v
    if caduca is not None and time.monotonic() > caduca:
        DATOS.pop(k, None)
        return None
    return dato


def barrer(parar):
    """La otra mitad de la expiracion.

    El borrado perezoso libera lo que se pide. Esto libera lo que NADIE vuelve a pedir, que si no
    crece para siempre. Redis muestrea claves al azar; aqui, como el objetivo es ensenarlo y no
    batir marcas, se recorre entero cada segundo.
    """
    while not parar.wait(1.0):
        ahora = time.monotonic()
        with CANDADO:
            for k in [k for k, (_, c) in DATOS.items() if c is not None and ahora > c]:
                DATOS.pop(k, None)


# ───────────────────────────────────────────────────────────────── RESP ──

def bulk(s):
    if s is None:
        return b"$-1\r\n"
    b = s.encode() if isinstance(s, str) else s
    return b"$%d\r\n%s\r\n" % (len(b), b)


def err_args(orden):
    return b"-ERR wrong number of arguments for '%s' command\r\n" % orden.lower().encode()


def leer_orden(f):
    """Lee UNA orden del cliente.

    RESP es TEXTO, y ahi esta media gracia del video: una orden es un array de cadenas con la
    longitud por delante.

        *3\r\n $3\r\nSET\r\n $3\r\nfoo\r\n $3\r\nbar\r\n

    Tambien se acepta la forma "inline" (una linea suelta con espacios) porque es lo que manda
    netcat, y en el video se ensena conectando con netcat.
    """
    linea = f.readline()
    if not linea:
        return None
    linea = linea.rstrip(b"\r\n")
    if not linea:
        return []
    if not linea.startswith(b"*"):
        return [p.decode("utf-8", "replace") for p in linea.split()]  # inline: netcat, telnet
    n = int(linea[1:])
    partes = []
    for _ in range(n):
        cab = f.readline().rstrip(b"\r\n")          # $<longitud>
        largo = int(cab[1:])
        partes.append(f.read(largo).decode("utf-8", "replace"))
        f.read(2)                                    # el \r\n del final
    return partes


# ───────────────────────────────────────────────────────────── comandos ──

def ejecutar(partes):
    if not partes:
        return b"-ERR peticion vacia\r\n"
    orden = partes[0].upper()
    args = partes[1:]

    if orden == "PING":
        return bulk(args[0]) if len(args) == 1 else b"+PONG\r\n"

    if orden == "ECHO":
        return bulk(args[0]) if len(args) == 1 else err_args(orden)

    # redis-cli manda COMMAND DOCS nada mas conectarse. Si no contestas algo, se queda esperando
    # y parece que el servidor esta roto. Un array vacio le vale.
    if orden == "COMMAND":
        return b"*0\r\n"

    if orden == "SET":
        if len(args) < 2:
            return err_args(orden)
        caduca = None
        for i in range(2, len(args) - 1, 2):        # SET k v EX <seg> / PX <ms>
            try:
                n = int(args[i + 1])
            except ValueError:
                return b"-ERR value is not an integer or out of range\r\n"
            if args[i].upper() == "EX":
                caduca = time.monotonic() + n
            elif args[i].upper() == "PX":
                caduca = time.monotonic() + n / 1000.0
        with CANDADO:
            DATOS[args[0]] = (args[1], caduca)
        return b"+OK\r\n"

    if orden == "GET":
        if len(args) != 1:
            return err_args(orden)
        with CANDADO:
            return bulk(vivo(args[0]))

    if orden == "DEL":
        with CANDADO:
            n = 0
            for k in args:
                if vivo(k) is not None:
                    DATOS.pop(k, None)
                    n += 1
        return b":%d\r\n" % n

    if orden == "EXISTS":
        with CANDADO:
            return b":%d\r\n" % sum(1 for k in args if vivo(k) is not None)

    if orden == "EXPIRE":
        if len(args) != 2:
            return err_args(orden)
        try:
            seg = int(args[1])
        except ValueError:
            return b"-ERR value is not an integer or out of range\r\n"
        with CANDADO:
            d = vivo(args[0])
            if d is None:
                return b":0\r\n"
            DATOS[args[0]] = (d, time.monotonic() + seg)
        return b":1\r\n"

    if orden == "TTL":
        if len(args) != 1:
            return err_args(orden)
        with CANDADO:
            if vivo(args[0]) is None:
                return b":-2\r\n"                     # no existe
            _, caduca = DATOS[args[0]]
            if caduca is None:
                return b":-1\r\n"                     # existe y no caduca
            import math
            # Hacia ARRIBA, como el Redis de verdad: recien puesto un EX 2, TTL contesta 2, no 1.
            return b":%d\r\n" % int(math.ceil(caduca - time.monotonic()))

    if orden in ("INCR", "DECR"):
        if len(args) != 1:
            return err_args(orden)
        paso = 1 if orden == "INCR" else -1
        with CANDADO:
            d = vivo(args[0])
            if d is None:
                n = 0
                caduca = None
            else:
                try:
                    n = int(d)
                except ValueError:
                    return b"-ERR value is not an integer or out of range\r\n"
                caduca = DATOS[args[0]][1]           # INCR no reinicia el reloj de la clave
            n += paso
            DATOS[args[0]] = (str(n), caduca)
        return b":%d\r\n" % n

    if orden == "DBSIZE":
        with CANDADO:
            return b":%d\r\n" % sum(1 for k in list(DATOS) if vivo(k) is not None)

    if orden in ("FLUSHALL", "FLUSHDB"):
        with CANDADO:
            DATOS.clear()
        return b"+OK\r\n"

    if orden == "QUIT":
        return b"+OK\r\n"

    return b"-ERR unknown command '%s'\r\n" % partes[0].encode()


# ─────────────────────────────────────────────────────────── el servidor ──

class Cliente(socketserver.StreamRequestHandler):
    # Sin retraso de Nagle: si no, las respuestas cortas se acumulan y redis-benchmark mide mal.
    disable_nagle_algorithm = True

    def handle(self):
        while True:
            try:
                partes = leer_orden(self.rfile)
            except (ValueError, IndexError, ConnectionError):
                return
            if partes is None:
                return
            if not partes:
                continue
            self.wfile.write(ejecutar(partes))
            if partes[0].upper() == "QUIT":
                return


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    address_family = socket.AF_INET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=6380)
    # Por defecto SOLO local. Se abre a 0.0.0.0 unicamente para la prueba con los clientes
    # oficiales, que corren dentro de un contenedor.
    ap.add_argument("--bind", default="127.0.0.1")
    a = ap.parse_args()

    parar = threading.Event()
    threading.Thread(target=barrer, args=(parar,), daemon=True).start()
    with Servidor((a.bind, a.puerto), Cliente) as s:
        print(f"escuchando en {a.bind}:{a.puerto}", flush=True)
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            parar.set()


if __name__ == "__main__":
    main()
