import re
from pathlib import Path

RE_INPUT = re.compile(r'\\(input|include){([^}]*)}')
RE_TITLE = re.compile(r'\\title{([^}]*)}')
RE_AUTHOR = re.compile(r'\\author{([^}]*)}')
RE_ABSTRACT = re.compile(r'\\begin{abstract}(.*?)\\end{abstract}', re.S)
RE_SECTION = re.compile(r'\\section{([^}]*)}')
RE_INCLUDEGRAPHICS = re.compile(r'\\includegraphics(?:\[[^\]]*\])?{([^}]*)}')

def read_file(path: Path):
    return path.read_text(encoding="utf-8")

def expand_inputs(tex: str, base_dir: Path, visited=None):
    if visited is None:
        visited = set()

    def replacer(match):
        rel_path = match.group(2)
        if not rel_path.endswith(".tex"):
            rel_path += ".tex"

        full_path = (base_dir / rel_path).resolve()
        if full_path in visited or not full_path.exists():
            return ""

        visited.add(full_path)
        content = read_file(full_path)
        return expand_inputs(content, full_path.parent, visited)

    return RE_INPUT.sub(replacer, tex)

def strip_latex(text):
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:{[^}]*})?', '', text)
    text = re.sub(r'[{}]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_latex(tex_path):
    tex_path = Path(tex_path)
    raw_tex = read_file(tex_path)

    # 🔑 EXPAND \input{} FILES
    tex = expand_inputs(raw_tex, tex_path.parent)

    title = RE_TITLE.search(tex)
    author = RE_AUTHOR.search(tex)
    abstract = RE_ABSTRACT.search(tex)

    metadata = {
        "title": title.group(1) if title else "Untitled",
        "author": author.group(1) if author else "",
        "abstract": strip_latex(abstract.group(1)) if abstract else ""
    }

    sections = []
    parts = RE_SECTION.split(tex)
    it = iter(parts)
    _ = next(it, None)

    while True:
        try:
            sec_title = next(it)
            sec_body = next(it)
        except StopIteration:
            break

        sections.append({
            "title": sec_title,
            "content": strip_latex(sec_body),
            "figures": RE_INCLUDEGRAPHICS.findall(sec_body)
        })

    return metadata, sections
