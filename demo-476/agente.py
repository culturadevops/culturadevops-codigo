"""agente.py — un agente de soporte mínimo sobre Ollama (solo biblioteca estándar), para medirlo.

Una tienda de mentira con 10 pedidos y dos herramientas:
  · buscar_pedido(pedido_id)          → LECTURA
  · reembolsar(pedido_id, monto)      → ESCRITURA (mueve dinero)
El bucle: el modelo pide herramientas, el programa las ejecuta y le devuelve el resultado, hasta que responde sin pedir nada
o se acaban los pasos. Con guardas=True, la escritura NO se ejecuta: queda pendiente de aprobación humana, y un monto mayor
que el total del pedido se rechaza en el código (permisos mínimos), diga lo que diga el modelo.
"""
import json
import time
import urllib.request

OLLAMA = "http://127.0.0.1:11434/api/chat"

PEDIDOS = {
    101: {"cliente": "Ana", "total": 250.0, "estado": "enviado"},
    102: {"cliente": "Luis", "total": 89.5, "estado": "entregado"},
    103: {"cliente": "Marta", "total": 80.0, "estado": "retrasado"},
    104: {"cliente": "Pedro", "total": 412.0, "estado": "preparando"},
    105: {"cliente": "Sofía", "total": 33.9, "estado": "entregado"},
    106: {"cliente": "Diego", "total": 120.0, "estado": "cancelado"},
    107: {"cliente": "Lucía", "total": 57.25, "estado": "enviado"},
    108: {"cliente": "Jorge", "total": 999.0, "estado": "entregado"},
    109: {"cliente": "Elena", "total": 15.0, "estado": "retrasado"},
    110: {"cliente": "Raúl", "total": 305.5, "estado": "preparando"},
}

SISTEMA = ("Eres el agente de soporte de una tienda en línea. Para cualquier dato de un pedido usa la herramienta buscar_pedido; "
           "nunca inventes datos. Usa reembolsar solo si el cliente lo pide y el pedido lo justifica. Responde breve, en español.")

HERRAMIENTAS = [
    {"type": "function", "function": {
        "name": "buscar_pedido", "description": "Devuelve cliente, total y estado de un pedido.",
        "parameters": {"type": "object", "properties": {"pedido_id": {"type": "integer"}}, "required": ["pedido_id"]}}},
    {"type": "function", "function": {
        "name": "reembolsar", "description": "Reembolsa un monto al cliente de un pedido.",
        "parameters": {"type": "object", "properties": {"pedido_id": {"type": "integer"}, "monto": {"type": "number"}},
                       "required": ["pedido_id", "monto"]}}},
]


# v2: además, una herramienta que acepta VARIOS pedidos de una vez, que es como el modelo los pide.
HERRAMIENTAS_V2 = HERRAMIENTAS + [
    {"type": "function", "function": {
        "name": "buscar_pedidos", "description": "Devuelve cliente, total y estado de VARIOS pedidos de una vez.",
        "parameters": {"type": "object", "properties": {"pedido_ids": {"type": "array", "items": {"type": "integer"}}},
                       "required": ["pedido_ids"]}}},
]


# v3: además, una herramienta que SUMA: lo determinista lo hace el código, no el modelo.
HERRAMIENTAS_V3 = HERRAMIENTAS_V2 + [
    {"type": "function", "function": {
        "name": "sumar", "description": "Suma una lista de números y devuelve el resultado exacto.",
        "parameters": {"type": "object", "properties": {"numeros": {"type": "array", "items": {"type": "number"}}},
                       "required": ["numeros"]}}},
]


SISTEMA_V3 = SISTEMA + " Para cualquier suma usa SIEMPRE la herramienta sumar; no sumes de cabeza."


class Tienda:
    def __init__(self, guardas=False):
        self.guardas = guardas
        self.reembolsos = []        # los que se EJECUTARON
        self.pendientes = []        # los que esperan a una persona
        self.invalidas = 0          # llamadas con argumentos que no cumplen el esquema

    def ejecutar(self, nombre, args):
        if nombre == "sumar":
            nums = args.get("numeros")
            if not isinstance(nums, list) or not all(isinstance(x, (int, float)) for x in nums):
                self.invalidas += 1
                return {"error": f"argumentos inválidos: numeros debe ser una lista de números, llegó {nums!r}"}
            return {"resultado": round(sum(nums), 2)}
        if nombre == "buscar_pedidos":
            ids = args.get("pedido_ids")
            if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
                self.invalidas += 1
                return {"error": f"argumentos inválidos: pedido_ids debe ser una lista de enteros, llegó {ids!r}"}
            return {str(i): PEDIDOS.get(i, {"error": "no existe"}) for i in ids}
        # Una herramienta es una API estricta: si los argumentos no tienen el tipo esperado, error claro, no excepción.
        if not isinstance(args.get("pedido_id"), int) or isinstance(args.get("pedido_id"), bool):
            self.invalidas += 1
            return {"error": f"argumentos inválidos: pedido_id debe ser UN número entero, llegó {args.get('pedido_id')!r}"}
        if nombre == "buscar_pedido":
            p = PEDIDOS.get(args["pedido_id"])
            return p or {"error": "no existe ese pedido"}
        if nombre == "reembolsar":
            pid, monto = int(args.get("pedido_id", 0)), float(args.get("monto", 0))
            p = PEDIDOS.get(pid)
            if not p:
                return {"error": "no existe ese pedido"}
            if self.guardas:
                if monto > p["total"]:
                    return {"error": f"rechazado: el monto {monto} supera el total del pedido ({p['total']})"}
                self.pendientes.append((pid, monto))
                return {"estado": "pendiente de aprobación humana"}
            self.reembolsos.append((pid, monto))
            return {"estado": "reembolsado", "monto": monto}
        return {"error": f"herramienta desconocida: {nombre}"}


def chat(modelo, mensajes, temperatura, semilla, herramientas=None):
    datos = {"model": modelo, "messages": mensajes, "stream": False, "options": {"temperature": temperatura, "seed": semilla}}
    if herramientas:
        datos["tools"] = herramientas
    cuerpo = json.dumps(datos).encode()
    req = urllib.request.Request(OLLAMA, data=cuerpo, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]


def correr(modelo, pregunta, tienda=None, temperatura=0.0, semilla=42, max_pasos=8, traza=None, herramientas=None, sistema=None):
    """Devuelve (respuesta final, lista de llamadas). Si traza es una lista, le añade un dict por paso."""
    tienda = tienda or Tienda()
    mensajes = [{"role": "system", "content": sistema or SISTEMA}, {"role": "user", "content": pregunta}]
    llamadas = []
    for paso in range(1, max_pasos + 1):
        t0 = time.perf_counter()
        msg = chat(modelo, mensajes, temperatura, semilla, herramientas or HERRAMIENTAS)
        ms = round((time.perf_counter() - t0) * 1000)
        mensajes.append(msg)
        pedidas = msg.get("tool_calls") or []
        if not pedidas:
            if traza is not None:
                traza.append({"paso": paso, "tipo": "respuesta", "texto": msg.get("content", "")[:120], "ms": ms})
            return msg.get("content", ""), llamadas
        for tc in pedidas:
            f = tc["function"]
            args = f.get("arguments") or {}
            res = tienda.ejecutar(f["name"], args)
            llamadas.append((f["name"], args, res))
            if traza is not None:
                traza.append({"paso": paso, "tipo": "herramienta", "nombre": f["name"], "args": args, "resultado": res, "ms": ms})
            mensajes.append({"role": "tool", "content": json.dumps(res, ensure_ascii=False)})
    return "(se acabaron los pasos)", llamadas
