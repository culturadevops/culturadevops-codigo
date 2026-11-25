"""medir_llm.py — mide un LLM local en Ollama: arranque en frío, tiempo hasta el primer token (TTFT) y tokens por segundo.

    python medir_llm.py <modelo> [<modelo> ...] [--rondas 3] [--cpu]

Solo biblioteca estándar. Por cada modelo: lo descarga de memoria (keep_alive 0), hace una petición en frío y N en caliente,
con streaming. TTFT = desde que mando la petición hasta el primer trozo con texto. tokens/s = eval_count / eval_duration que
devuelve Ollama en el último trozo. --cpu fuerza num_gpu=0 (todo en la CPU), para simular una máquina sin GPU.
"""
import json
import statistics
import sys
import time
import urllib.request

URL = "http://127.0.0.1:11434/api/generate"
PROMPT = "Explica en tres frases qué es un contenedor de Docker."


def post(cuerpo):
    return urllib.request.urlopen(urllib.request.Request(URL, data=json.dumps(cuerpo).encode(),
                                                         headers={"Content-Type": "application/json"}), timeout=900)


def cargados():
    with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=10) as r:
        return [m["name"] for m in json.loads(r.read()).get("models", [])]


def descargar(modelo):
    """Saca el modelo de memoria y ESPERA a que /api/ps confirme que ya no está: si no, el «frío» sale caliente."""
    post({"model": modelo, "keep_alive": 0}).read()
    for _ in range(120):
        if modelo not in cargados():
            return
        time.sleep(0.5)
    raise SystemExit(f"{modelo} sigue cargado: no mido un frío que no es frío")


def una(modelo, cpu):
    opciones = {"temperature": 0, "seed": 42, "num_predict": 128}
    if cpu:
        opciones["num_gpu"] = 0
    t0 = time.perf_counter()
    ttft = None
    with post({"model": modelo, "prompt": PROMPT, "stream": True, "options": opciones}) as r:
        for linea in r:
            d = json.loads(linea)
            if ttft is None and d.get("response"):
                ttft = time.perf_counter() - t0
            if d.get("done"):
                total = time.perf_counter() - t0
                return {"ttft": ttft, "total": total, "tokens": d["eval_count"],
                        "tps": d["eval_count"] / (d["eval_duration"] / 1e9), "carga": d.get("load_duration", 0) / 1e9}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rondas = int(sys.argv[sys.argv.index("--rondas") + 1]) if "--rondas" in sys.argv else 3
    args = [a for a in args if a != str(rondas)]
    cpu = "--cpu" in sys.argv
    print(f"prompt: {PROMPT!r} · máx. 128 tokens · temperatura 0 · {'SOLO CPU' if cpu else 'GPU'}")
    print(f"{'modelo':22} {'frío: carga':>11} {'frío: TTFT':>10} {'TTFT caliente':>13} {'tokens/s':>9}")
    for m in cargados():                 # empezar con la memoria vacía
        descargar(m)
    for m in args:
        descargar(m)
        frio = una(m, cpu)
        calientes = [una(m, cpu) for _ in range(rondas)]
        ttft = statistics.median(c["ttft"] for c in calientes)
        tps = statistics.median(c["tps"] for c in calientes)
        print(f"{m:22} {frio['carga']:>9.2f} s {frio['ttft']:>8.2f} s {ttft * 1000:>10.0f} ms {tps:>9.1f}")
        descargar(m)


if __name__ == "__main__":
    main()
