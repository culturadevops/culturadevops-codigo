# -*- coding: utf-8 -*-
"""Diagramas 1920x1080 de los vídeos de AWS Chatbot (357-359): HTML → PNG con tools/imagen/html2png.js.
Todo lo que dibujan sale de la documentación oficial (fuentes en cada builder).

    python diagramas.py
"""
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TMP = AQUI / "_diagramas"
OUT = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\aws-chatbot")
H2P = Path(r"<proyecto>\tools\imagen\html2png.js")

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1920px;height:1080px;background:#0d1117;color:#e6edf3;font-family:Arial,Helvetica,sans-serif;
     display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 80px 60px}
h1{font-family:'Arial Black',Arial;font-size:58px;margin-bottom:56px;text-align:center}
.fila{display:flex;align-items:center;gap:26px}
.caja{border:4px solid var(--c);border-radius:22px;padding:26px 28px;background:#161b22;text-align:center;min-width:250px}
.caja b{display:block;font-family:'Arial Black',Arial;font-size:34px;color:var(--c);margin-bottom:10px}
.caja span{font-size:25px;color:#c9d1d9;line-height:1.35}
.flecha{font-size:64px;color:#8b949e}
.pie{margin-top:46px;font-size:26px;color:#8b949e;text-align:center;line-height:1.5}
.pila{display:flex;flex-direction:column;gap:16px}
.pila .caja{min-width:300px;padding:16px 22px}
.pila .caja b{font-size:28px;margin:0}
"""


def pagina(cuerpo):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{cuerpo}</body></html>"


FLUJO = pagina("""
<h1>Cómo llega una alerta de AWS a tu chat</h1>
<div class="fila">
  <div class="pila">
    <div class="caja" style="--c:#ff9900"><b>CloudWatch</b><span>alarmas</span></div>
    <div class="caja" style="--c:#ff4f8b"><b>EventBridge</b><span>GuardDuty · Health · Config</span></div>
    <div class="caja" style="--c:#3fb950"><b>Budgets</b><span>alertas de presupuesto</span></div>
    <div class="caja" style="--c:#a371f7"><b>Tu app</b><span>notificación personalizada</span></div>
  </div>
  <div class="flecha">→</div>
  <div class="caja" style="--c:#ff4f8b"><b>Tema SNS</b><span>el único punto<br>de entrada</span></div>
  <div class="flecha">→</div>
  <div class="caja" style="--c:#4f8cff"><b>Amazon Q Developer</b><span>in chat applications<br>(antes AWS Chatbot)</span></div>
  <div class="flecha">→</div>
  <div class="pila">
    <div class="caja" style="--c:#e01e5a"><b>Slack</b><span>canal</span></div>
    <div class="caja" style="--c:#6264a7"><b>Teams</b><span>canal</span></div>
  </div>
</div>
<p class="pie">Todo pasa por un tema SNS · Chime: AWS terminó su soporte el 20-02-2026<br>
Fuente: docs.aws.amazon.com/chatbot — «Monitoring AWS services»</p>
""")

PERMISOS = pagina("""
<h1>Lo que de verdad puede hacer alguien desde el chat</h1>
<div class="fila">
  <div class="caja" style="--c:#4f8cff"><b>Rol IAM</b><span>del canal (todos igual)<br>o de cada usuario</span></div>
  <div class="flecha">∩</div>
  <div class="caja" style="--c:#ff9900"><b>Guardrails</b><span>políticas del canal<br>sin ellas: AdministratorAccess</span></div>
  <div class="flecha">−</div>
  <div class="caja" style="--c:#f85149"><b>Lista bloqueada</b><span>iam:* · sts:* · kms:*<br>secretsmanager:* · s3:GetObject…</span></div>
  <div class="flecha">=</div>
  <div class="caja" style="--c:#3fb950"><b>Permitido</b><span>lo que queda</span></div>
</div>
<p class="pie">Los guardrails mandan sobre el rol: un usuario con AdministratorAccess en un canal limitado queda limitado<br>
Fuente: docs.aws.amazon.com/chatbot — «Understanding permissions» · API CreateSlackChannelConfiguration</p>
""")


def main():
    TMP.mkdir(exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for nombre, html in (("flujo", FLUJO), ("permisos", PERMISOS)):
        src = TMP / f"{nombre}.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run(["node", str(H2P), "--in", str(src), "--out", str(OUT / f"{nombre}.png"),
                        "--width", "1920", "--height", "1080"], check=True)
        print(OUT / f"{nombre}.png")


if __name__ == "__main__":
    main()
