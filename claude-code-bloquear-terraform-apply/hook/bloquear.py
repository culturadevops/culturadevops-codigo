"""Hook PreToolUse (matcher Bash|PowerShell) del vídeo 709.

Lee el comando de tool_input.command, lo parte como lo haría el shell y busca el VERBO,
no el texto del principio: `terraform ... apply|destroy` y `kubectl ... delete`, en cualquier
posición, detrás de rutas, `env`, `timeout`, `bash -c '...'` o `&&`. Si lo encuentra, escribe el
motivo en stderr y sale con 2 («Blocks the tool call», hooks.md). Si el comando no se puede
leer y menciona terraform o kubectl, también bloquea: lo que no entiendo, no pasa.
"""
import json
import re
import shlex
import sys

PELIGRO = {"terraform": {"apply", "destroy"}, "tofu": {"apply", "destroy"}, "kubectl": {"delete"}}
ENVOLTURAS = {"env", "timeout", "nice", "nohup", "stdbuf", "command", "builtin", "exec", "sudo", "time", "xargs", "watch"}
SHELLS = {"bash", "sh", "zsh", "dash", "pwsh", "powershell", "cmd"}
OPS = {"&&", "||", ";", "|", "|&", "&", "\n"}
# opciones globales de kubectl que llevan valor separado: el valor no es el verbo
KUBE_CON_VALOR = {"--context", "-n", "--namespace", "--kubeconfig", "-s", "--server", "--cluster", "--user", "--as"}


def simples(cmd):
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    actual = []
    for tok in lex:
        if tok in OPS or set(tok) <= set(";&|"):
            if actual:
                yield actual
            actual = []
        else:
            actual.append(tok)
    if actual:
        yield actual


def programa(tok):
    return re.split(r"[\\/]", tok)[-1].lower().removesuffix(".exe")


def revisar(palabras, prof=0):
    i = 0
    while i < len(palabras) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", palabras[i]):
        i += 1  # VAR=valor delante
    while i < len(palabras) and programa(palabras[i]) in ENVOLTURAS:
        i += 1
        while i < len(palabras) and (palabras[i].startswith("-") or palabras[i][:1].isdigit() or "=" in palabras[i]):
            i += 1  # opciones y argumentos de la envoltura (timeout 60, env -i, VAR=x)
    if i >= len(palabras):
        return None
    prog, resto = programa(palabras[i]), palabras[i + 1:]
    if prog in SHELLS and prof < 3:
        for j, t in enumerate(resto):
            if t.lower() in ("-c", "-command", "/c") and j + 1 < len(resto):
                return analizar(" ".join(resto[j + 1:]), prof + 1)
    if prog in PELIGRO:
        k = 0
        while k < len(resto):
            t = resto[k]
            if t.startswith("-"):
                k += 2 if (prog == "kubectl" and t in KUBE_CON_VALOR) else 1
                continue
            return f"{prog} {t}" if t.lower() in PELIGRO[prog] else None
    return None


def analizar(cmd, prof=0):
    if re.search(r"\$\(|`|\beval\b", cmd) and re.search(r"terraform|tofu|kubectl", cmd):
        return "sustitución de comandos con terraform/kubectl (no se puede leer de antemano)"
    try:
        partes = list(simples(cmd))
    except ValueError:
        return "comando ilegible que menciona terraform/kubectl" if re.search(r"terraform|tofu|kubectl", cmd) else None
    for p in partes:
        motivo = revisar(p, prof)
        if motivo:
            return motivo
    return None


def main():
    sys.stderr.reconfigure(encoding="utf-8")
    datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    motivo = analizar(datos.get("tool_input", {}).get("command", ""))
    if motivo:
        print(f"Bloqueado por el hook del proyecto: «{motivo}». En este proyecto un agente no aplica ni borra "
              "infraestructura; deja el plan y que lo aplique una persona.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
