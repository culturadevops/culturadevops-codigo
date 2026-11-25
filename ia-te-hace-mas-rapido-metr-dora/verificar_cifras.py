# -*- coding: utf-8 -*-
"""Vídeo 712 (cultura-devops): cada cifra que sale en pantalla, buscada LITERAL en el original descargado.

1) fuentes/*.html se bajaron con curl el 2026-10-29 (fuentes_a_texto.py los pasa a .txt; el PDF de Cui et al. con pdftotext).
2) Este script busca cada cita en su .txt. Si una no aparece, la marca FALTA y sale con código 1: esa cifra no va al vídeo.
Uso:  python -I fuentes_a_texto.py && python -I verificar_cifras.py   →  SALIDA.md
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
F = AQUI / "fuentes"
CONSULTA = "2026-10-29"

# (id, quién paga / tipo, archivo, URL, cita literal que tiene que estar)
CIFRAS = [
    ("metr25_19", "independiente · RCT", "metr-2025.txt", "https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/",
     "they take 19% longer to complete issues"),
    ("metr25_percepcion", "independiente · RCT", "metr-2025.txt", "https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/",
     "developers expected AI to speed them up by 24%, and even after experiencing the slowdown, they still believed AI had sped them up by 20%"),
    ("metr25_muestra", "independiente · RCT", "metr-2025.txt", "https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/",
     "we recruited 16 experienced developers from large open-source repositories (averaging 22k+ stars and 1M+ lines of code)"),
    ("metr25_issues", "independiente · RCT", "metr-2025.txt", "https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/",
     "Developers provide lists of real issues (246 total)"),
    ("metr25_herramienta", "independiente · RCT", "metr-2025.txt", "https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/",
     "primarily Cursor Pro with Claude 3.5/3.7 Sonnet"),
    ("metr25_dos_horas", "independiente · RCT", "metr-2025.txt", "https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/",
     "which average two hours each"),
    ("metr25_obsoleto", "independiente · RCT", "metr-2025.txt", "https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/",
     "These results are out of date."),
    ("metr26_ic", "independiente · RCT", "metr-2026.txt", "https://metr.org/blog/2026-02-24-uplift-update/",
     "Our early 2025 study found the use of AI causes tasks to take 19% longer, with a confidence interval between +2% and +39%"),
    ("metr26_orig", "independiente · RCT", "metr-2026.txt", "https://metr.org/blog/2026-02-24-uplift-update/",
     "we now estimate a speedup of -18% with a confidence interval between -38% and +9%"),
    ("metr26_nuevos", "independiente · RCT", "metr-2026.txt", "https://metr.org/blog/2026-02-24-uplift-update/",
     "Among newly-recruited developers the estimated speedup is -4%, with a confidence interval between -15% and +9%"),
    ("metr26_muestra", "independiente · RCT", "metr-2026.txt", "https://metr.org/blog/2026-02-24-uplift-update/",
     "We have data from 57 developers, across 143 repos, and 800+ tasks"),
    ("metr26_debil", "independiente · RCT", "metr-2026.txt", "https://metr.org/blog/2026-02-24-uplift-update/",
     "our data is only very weak evidence for the size of this increase"),
    ("metr26_seleccion", "independiente · RCT", "metr-2026.txt", "https://metr.org/blog/2026-02-24-uplift-update/",
     "30% to 50% of developers told us that they were choosing not to submit some tasks because they did not want to do them without AI"),
    ("metr26_pago", "independiente · RCT", "metr-2026.txt", "https://metr.org/blog/2026-02-24-uplift-update/",
     "we reduced the pay from $150/hr to $50/hr"),
    ("dora24_estab", "Google Cloud (vende Gemini) · encuesta", "dora-2024.txt",
     "https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report",
     "an estimated decrease in delivery throughput by 1.5%, and an estimated reduction in delivery stability by 7.2%"),
    ("dora24_25", "Google Cloud (vende Gemini) · encuesta", "dora-2024.txt",
     "https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report",
     "A 25% increase in AI adoption is associated with improvements in several key areas: 7.5% increase in documentation quality 3.4% increase in code quality 3.1% increase in code review speed"),
    ("dora24_confianza", "Google Cloud (vende Gemini) · encuesta", "dora-2024.txt",
     "https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report",
     "39% of the respondents reported little to no trust in AI-generated code"),
    ("dora25_muestra", "Google Cloud (vende Gemini) · encuesta", "dora-2025.txt",
     "https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report",
     "survey responses from nearly 5,000 technology professionals"),
    ("dora25_90", "Google Cloud (vende Gemini) · encuesta", "dora-2025.txt",
     "https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report",
     "90% of survey respondents report using AI at work. More than 80% believe it has increased their productivity"),
    ("dora25_30", "Google Cloud (vende Gemini) · encuesta", "dora-2025.txt",
     "https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report",
     "30% report little or no trust in the code generated by AI"),
    ("dora25_throughput", "Google Cloud (vende Gemini) · encuesta", "dora-2025.txt",
     "https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report",
     "AI adoption does continue to have a negative relationship with software delivery stability"),
    ("dora25_amplifica", "Google Cloud (vende Gemini) · encuesta", "dora-2025.txt",
     "https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report",
     "AI doesn't fix a team; it amplifies what's already there"),
    ("peng_558", "GitHub/Microsoft · experimento", "peng-2023.txt", "https://arxiv.org/abs/2302.06590",
     "completed the task 55.8% faster than the control group"),
    ("gh_95", "GitHub/Microsoft · experimento", "github-copilot-blog.txt",
     "https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/",
     "We recruited 95 professional developers"),
    ("gh_tiempos", "GitHub/Microsoft · experimento", "github-copilot-blog.txt",
     "https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/",
     "took on average 1 hour and 11 minutes to complete the task, while the developers who didn"),
    ("gh_2h41", "GitHub/Microsoft · experimento", "github-copilot-blog.txt",
     "https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/",
     "took on average 2 hours and 41 minutes"),
    ("gh_ic", "GitHub/Microsoft · experimento", "github-copilot-blog.txt",
     "https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/",
     "the 95% confidence interval for the percentage speed gain is [21%, 89%]"),
    ("cui_26", "Microsoft en parte (2 de 6 autores) · 3 ensayos de campo", "cui-mit-draft.txt",
     "https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf",
     "when data is combined across three experiments and 4,867 developers, our analysis reveals a 26.08% increase (SE: 10.3%) in completed tasks"),
    ("cui_autores", "Microsoft en parte (2 de 6 autores) · 3 ensayos de campo", "cui-mit-draft.txt",
     "https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf",
     "Jaffe: Microsoft."),
    ("cui_novatos", "Microsoft en parte (2 de 6 autores) · 3 ensayos de campo", "cui-mit-draft.txt",
     "https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf",
     "less experienced developers had higher adoption rates and greater productivity gains"),
    ("google_21", "Google · RCT interno", "google-eca.txt", "https://arxiv.org/abs/2410.12944",
     "stands at about 21\\%, although our confidence interval is large"),
    ("google_96", "Google · RCT interno", "google-eca.txt", "https://arxiv.org/abs/2410.12944",
     "randomized controlled trial with 96 full-time Google software engineers"),
    ("so25_muestra", "Stack Overflow · encuesta", "so-2025.txt", "https://survey.stackoverflow.co/2025/",
     "over 49,000+ responses from 177 countries"),
    ("so25_84", "Stack Overflow · encuesta", "so-2025-ai.txt", "https://survey.stackoverflow.co/2025/ai",
     "84% of respondents are using or planning to use AI tools in their development process"),
    ("so25_46", "Stack Overflow · encuesta", "so-2025-ai.txt", "https://survey.stackoverflow.co/2025/ai",
     "More developers actively distrust the accuracy of AI tools (46%) than trust it (33%)"),
    ("so25_66", "Stack Overflow · encuesta", "so-2025-ai.txt", "https://survey.stackoverflow.co/2025/ai",
     "The biggest single frustration, cited by 66% of developers, is dealing with \"AI solutions that are almost right, but not quite,\""),
    ("so25_45", "Stack Overflow · encuesta", "so-2025-ai.txt", "https://survey.stackoverflow.co/2025/ai",
     "\"Debugging AI-generated code is more time-consuming\" (45%)"),
    ("so25_52", "Stack Overflow · encuesta", "so-2025-ai.txt", "https://survey.stackoverflow.co/2025/ai",
     "52% of developers agree that AI tools and/or AI agents have had a positive effect on their productivity"),
    ("so26_muestra", "Stack Overflow · encuesta", "so-2026.txt", "https://survey.stackoverflow.co/2026/",
     "30,903 Responses"),
    ("so26_48", "Stack Overflow · encuesta", "so-2026-ai.txt", "https://survey.stackoverflow.co/2026/ai",
     "48% indicate they trust AI when they can easily validate the answers and only 16% extend that trust"),
    ("so26_agentes", "Stack Overflow · encuesta", "so-2026-ai.txt", "https://survey.stackoverflow.co/2026/ai",
     "Claude Code (66%) and GitHub Copilot (59%) are the leaders for coding agents"),
    ("so26_73", "Stack Overflow · encuesta", "so-2026-ai.txt", "https://survey.stackoverflow.co/2026/ai",
     "use coding assistants and agents daily (73%)"),
    ("vera25_45", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2025.txt",
     "https://www.veracode.com/blog/genai-code-security-report/",
     "45% of code samples failed security tests and introduced OWASP Top 10 security vulnerabilities"),
    ("vera25_100", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2025.txt",
     "https://www.veracode.com/blog/genai-code-security-report/",
     "we tested over 100 large language models across Java, Python, C#, and JavaScript"),
    ("vera25_java", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2025.txt",
     "https://www.veracode.com/blog/genai-code-security-report/",
     "Java was the riskiest language, with a 72% security failure rate across tasks"),
    ("vera26_56", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2026.txt",
     "https://www.veracode.com/news/llms-are-getting-smarter-but-not-safer-veracode-2026-genai-code-security-report-finds-ai-generated-code-security-has-stalled-at-56%25-pass-rate/",
     "the average security pass rate sits at 56 percent — virtually unchanged since last year’s report"),
    ("vera26_sintaxis", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2026.txt",
     "https://www.veracode.com/news/llms-are-getting-smarter-but-not-safer-veracode-2026-genai-code-security-report-finds-ai-generated-code-security-has-stalled-at-56%25-pass-rate/",
     "syntax pass rate of ~100 percent"),
    ("vera26_gpt", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2026.txt",
     "https://www.veracode.com/news/llms-are-getting-smarter-but-not-safer-veracode-2026-genai-code-security-report-finds-ai-generated-code-security-has-stalled-at-56%25-pass-rate/",
     "OpenAI’s GPT-5.5 leads this year’s report at 68 percent"),
    ("vera26_lenguajes", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2026.txt",
     "https://www.veracode.com/news/llms-are-getting-smarter-but-not-safer-veracode-2026-genai-code-security-report-finds-ai-generated-code-security-has-stalled-at-56%25-pass-rate/",
     "range from Python at 63 percent down to Java at only 30 percent"),
    ("vera26_sin_prompt", "Veracode (vende análisis de seguridad) · banco de pruebas", "veracode-2026.txt",
     "https://www.veracode.com/news/llms-are-getting-smarter-but-not-safer-veracode-2026-genai-code-security-report-finds-ai-generated-code-security-has-stalled-at-56%25-pass-rate/",
     "under standardized conditions with no security-specific prompting"),
]

# Cifras del informe base que NO entran: no aparecen en el texto del original abierto.
FUERA = [
    ("Veracode 2026: Claude Opus 4.8 al 62 %", "veracode-2026.txt", "Opus 4.8"),
    ("DORA 2024: tamaño de la muestra (39.000)", "dora-2024.txt", "39,000"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    L = ["# SALIDA — vídeo 712 (cultura-devops) «¿La IA te hace programar más rápido?»", "",
         f"Originales descargados con curl el {CONSULTA} en `fuentes/`. Cada cita se buscó literal en su texto "
         "(`python -I verificar_cifras.py`).", "", "| id | quién lo publica · tipo | cita literal | archivo | ¿está? |", "|---|---|---|---|---|"]
    faltan = 0
    for i, quien, arch, url, cita in CIFRAS:
        t = (F / arch).read_text(encoding="utf-8", errors="replace")
        ok = cita in " ".join(t.split())
        faltan += not ok
        L.append(f"| {i} | {quien} | «{cita}» | [{arch}]({url}) | {'sí' if ok else 'FALTA'} |")
    L += ["", "## Del informe base, fuera del vídeo", "", "| cifra | archivo | ¿aparece en el original? |", "|---|---|---|"]
    for d, arch, pat in FUERA:
        t = (F / arch).read_text(encoding="utf-8", errors="replace")
        L.append(f"| {d} | {arch} | {'sí' if pat in t else 'no → fuera'} |")
    L += ["", f"Citas verificadas: {len(CIFRAS) - faltan} de {len(CIFRAS)}."]
    (AQUI / "SALIDA.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"verificadas {len(CIFRAS) - faltan}/{len(CIFRAS)}")
    sys.exit(1 if faltan else 0)


if __name__ == "__main__":
    main()
