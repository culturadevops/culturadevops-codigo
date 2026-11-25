INVOCACIONES = 0


def suma(n):
    s = 0
    for i in range(1, n + 1):
        s += (i * i) % 1000003
    return s


def handler(event, context):
    global INVOCACIONES
    INVOCACIONES += 1
    return {"lang": "python", "fn": "simple", "suma": suma(10000), "invocacion": INVOCACIONES}
