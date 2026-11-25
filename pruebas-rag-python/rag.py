# -*- coding: utf-8 -*-
"""RAG en Python sin framework: psycopg + pgvector + Ollama por HTTP (urllib de la biblioteca estándar).
Vídeo 797 de cultura-devops. Una sola dependencia: psycopg.

    python rag.py indexar
    python rag.py buscar "pregunta"
    python rag.py preguntar "pregunta"
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

import psycopg

OLLAMA = os.environ.get("OLLAMA", "http://host.docker.internal:11434")
PG = os.environ.get("PG", "postgresql://postgres:demo@cd797-pg:5432/postgres")
EMB = os.environ.get("EMB", "nomic-embed-text")
LLM = os.environ.get("LLM", "qwen2.5:7b")
PREFIJOS = os.environ.get("PREFIJOS", "1") == "1" and EMB.startswith("nomic")   # nomic-embed-text pide «search_document:» y «search_query:»
UMBRAL = float(os.environ.get("UMBRAL", "0"))         # 0 = sin umbral
DOCS = Path(__file__).parent / "docs"


def ollama(ruta, cuerpo):
    req = urllib.request.Request(OLLAMA + ruta, data=json.dumps(cuerpo).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def embeber(textos):
    return ollama("/api/embed", {"model": EMB, "input": textos})["embeddings"]


def vec(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def trocear(ruta):
    """Un trozo por párrafo; el título del documento va delante para que el trozo se entienda solo."""
    lineas = ruta.read_text(encoding="utf-8").strip().split("\n\n")
    titulo = lineas[0].lstrip("# ").strip()
    return [(ruta.stem, n, f"{titulo}. {p.strip()}") for n, p in enumerate(lineas[1:], start=1)]


def indexar():
    trozos = [t for doc in sorted(DOCS.glob("*.md")) for t in trocear(doc)]
    pref = "search_document: " if PREFIJOS else ""
    vectores = embeber([pref + t[2] for t in trozos])
    with psycopg.connect(PG, autocommit=True) as con:
        con.execute("CREATE EXTENSION IF NOT EXISTS vector")
        con.execute("DROP TABLE IF EXISTS trozos")
        con.execute(f"CREATE TABLE trozos (id serial PRIMARY KEY, doc text, n int, texto text, emb vector({len(vectores[0])}))")
        for (doc, n, texto), v in zip(trozos, vectores):
            con.execute("INSERT INTO trozos (doc, n, texto, emb) VALUES (%s, %s, %s, %s::vector)", (doc, n, texto, vec(v)))
        con.execute("CREATE INDEX ON trozos USING hnsw (emb vector_cosine_ops)")
        total = con.execute("SELECT count(*), count(DISTINCT doc) FROM trozos").fetchone()
    print(f"indexados {total[0]} trozos de {total[1]} documentos · {len(vectores[0])} números por trozo")


def buscar(pregunta, k=int(os.environ.get("K", "3"))):
    pref = "search_query: " if PREFIJOS else ""
    q = vec(embeber([pref + pregunta])[0])
    with psycopg.connect(PG) as con:
        return con.execute("SELECT doc, n, texto, emb <=> %s::vector AS dist FROM trozos ORDER BY emb <=> %s::vector LIMIT %s",
                           (q, q, k)).fetchall()


def preguntar(pregunta):
    filas = buscar(pregunta)
    for doc, n, _, dist in filas:
        print(f"  [{doc}#{n}] distancia {dist:.3f}")
    if UMBRAL and filas[0][3] > UMBRAL:
        print(f"respuesta: no lo encuentro en los documentos (el más cercano está a {filas[0][3]:.3f} > {UMBRAL})")
        return
    contexto = "\n".join(f"[{doc}#{n}] {texto}" for doc, n, texto, _ in filas)
    sistema = ("Responde en español y SOLO con la información del contexto. Cita entre corchetes el trozo que usas, "
               "por ejemplo [despliegues#1]. Si el contexto no tiene la respuesta, di exactamente: "
               "«No está en los documentos.»")
    r = ollama("/api/chat", {"model": LLM, "stream": False, "options": {"temperature": 0, "seed": 7},
                             "messages": [{"role": "system", "content": sistema},
                                          {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"}]})
    print("respuesta:", r["message"]["content"].strip())


if __name__ == "__main__":
    accion = sys.argv[1]
    if accion == "indexar":
        indexar()
    elif accion == "buscar":
        for doc, n, texto, dist in buscar(sys.argv[2]):
            print(f"  {dist:.3f}  [{doc}#{n}] {texto[:70]}...")
    elif accion == "preguntar":
        preguntar(sys.argv[2])
