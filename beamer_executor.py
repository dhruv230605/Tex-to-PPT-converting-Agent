from pathlib import Path
import os

BEAMER_HEADER = r"""
\documentclass{beamer}
\usetheme{Madrid}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{booktabs}
\title{%s}
\author{%s}
\begin{document}
\frame{\titlepage}
"""

BEAMER_FOOTER = r"\end{document}"

def generate_beamer(metadata, slide_plans, image_base, out_file):
    tex = BEAMER_HEADER % (metadata["title"], metadata["author"])

    if metadata["abstract"]:
        tex += r"\begin{frame}{Abstract}" + "\n"
        tex += metadata["abstract"] + "\n"
        tex += r"\end{frame}" + "\n\n"

    for plan in slide_plans:
        for slide in plan["slides"]:
            tex += r"\begin{frame}{" + slide["title"] + "}\n"
            tex += r"\begin{itemize}" + "\n"
            for bullet in slide["bullets"]:
                tex += r"\item " + bullet + "\n"
            tex += r"\end{itemize}" + "\n"

            for fig in slide.get("figures", []):
                fig_path = os.path.join(image_base, fig)
                if os.path.exists(fig_path):
                    tex += r"\begin{center}" + "\n"
                    tex += r"\includegraphics[height=0.6\textheight]{" + fig + "}\n"
                    tex += r"\end{center}" + "\n"

            tex += r"\end{frame}" + "\n\n"

    tex += BEAMER_FOOTER
    Path(out_file).write_text(tex, encoding="utf-8")
