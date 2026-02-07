# TeX2Slides — Self-Reflective LLM Agent for Paper → Slides

TeX2Slides is a self-reflective LLM agent that converts LaTeX research papers into
professional PowerPoint presentations using intelligent planning and optional LLM-driven reflection.

**Output Format:**
- PowerPoint (PPTX) — primary and only renderer

**Architecture:**
Planner → Refiner → StyleAgent (with optional LLM reflection) → PPTX Executor

- The LLM plans slide content from paper sections
- The LLM refines through multi-round critique loops
- The StyleAgent optimizes design (deterministic or LLM-driven reflection)
- A deterministic executor generates final PPTX files
- No agent frameworks required (AutoGen, LangGraph, n8n, etc.)

---

## Features

- **Multi-file LaTeX support** — handles `\input{}` and `\include{}` directives
- **LLM-based planning** — extracts sections and figures into structured slide plans
- **Multi-round refinement** — iterative critique loop for content improvement
- **Optional LLM reflection** — advanced design critique with `--use-reflection` flag
- **Template support** — optional PPTX master slide compatibility via `--template` flag
- **Smart text handling** — automatic bullet conversion, emoji/LaTeX cleanup, word wrapping
- **Image embedding** — PNG, JPG, SVG support (PDF images gracefully skipped)
- **Analogy & Q&A slides** — specialized layouts with strict Comic Sans MS 28pt styling
- **Clear architecture** — LLM produces auditable JSON plans; executor is pure deterministic
- **No LaTeX dependencies** — pure Python pipeline; no pdflatex, dvips, or Beamer required

---

## Pipeline Architecture

```
LaTeX Paper (.tex)
    ↓
[Parser] Extract sections, figures, metadata
    ↓
[SlidePlanner] LLM: generate initial slide plan (JSON)
    ↓
[SlideRefiner] LLM: multi-round critique + refinement
    ↓
[StyleAgent] Optimize design (deterministic or LLM-driven)
    ↓
[PPTX Executor] Generate PowerPoint file
    ↓
paper_slides.pptx ✓
```

All LLM outputs are structured JSON; executors never make API calls.

---

## Project Structure

```
tex2slides_agent/
├── src/
│   ├── cli/
│   │   └── main.py          # CLI entrypoint
│   ├── parser/
│   │   └── latex_parser.py  # LaTeX → JSON extractor
│   ├── llm/
│   │   ├── llm_base.py      # Shared LLM infrastructure
│   │   ├── slide_planner.py # Initial slide planning
│   │   ├── slide_refiner.py # Multi-round refinement
│   │   ├── slide_critic.py  # Critique logic
│   │   └── style_agent.py   # Design optimization + reflection
│   └── executors/
│       └── pptx_executor.py # PPTX renderer (sole backend)
├── requirements.txt
├── README.md
└── outputs/                 # Generated slides (e.g., paper_slides.pptx)
```

---

## Input Format

Input must be the root LaTeX file of the paper.

Examples:
- iclr2023_conference.tex
- ms.tex

Multi-file projects using \input{} are fully supported.

Do NOT pass:
- A directory
- Individual section files

---

## Installation

Clone the repository and install the Python dependencies:

```bash
git clone https://github.com/<your-username>/tex2slides_agent.git
cd tex2slides_agent
pip install -r requirements.txt
```

This project is now PPTX-first and has no runtime LaTeX compilation dependency.

---

## Usage

### Basic: Generate PPTX Slides

```bash
cd /path/to/tex2slides_agent
PYTHONPATH=. python3 src/cli/main.py \
  --input /path/to/paper.tex \
  --out paper_slides.pptx \
  --api-key YOUR_OPENAI_API_KEY
```

### With Template (Optional)

Apply a custom PPTX template (preserves master slides and layout definitions):

```bash
PYTHONPATH=. python3 src/cli/main.py \
  --input /path/to/paper.tex \
  --out paper_slides.pptx \
  --template /path/to/template.pptx \
  --api-key YOUR_OPENAI_API_KEY
```

### With LLM Reflection (Optional)

Enable iterative LLM-driven design critique and refinement:

```bash
PYTHONPATH=. python3 src/cli/main.py \
  --input /path/to/paper.tex \
  --out paper_slides.pptx \
  --use-reflection \
  --rounds 2 \
  --api-key YOUR_OPENAI_API_KEY
```

### Full Example with All Options

```bash
PYTHONPATH=. python3 src/cli/main.py \
  --input /Users/dhruv/Documents/papers/transformer.tex \
  --out transformer_slides.pptx \
  --template /Users/dhruv/Documents/templates/corporate.pptx \
  --use-reflection \
  --rounds 3 \
  --api-key sk-...
```

---

## CLI Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--input` | str | **required** | Path to root LaTeX file |
| `--out` | str | **required** | Output PPTX file path |
| `--api-key` | str | `OPENAI_API_KEY` env | OpenAI API key |
| `--template` | str | None | Optional PPTX template file (applies master layouts) |
| `--use-reflection` | flag | False | Enable LLM-driven design reflection loop |
| `--rounds` | int | 2 | Number of refinement rounds (Refiner and StyleAgent) |

---

## Key Features Explained

### 1. Analogy Slides
Automatically inserted for complex concepts. Rendered with:
- Title: "Analogy: {concept}"
- Font: Comic Sans MS, 28pt, bold, white
- Background: #FFA46B (light orange)

### 2. Q&A Slides
Encourage reader engagement after major sections. Rendered with:
- Title: "Q&A"
- Font: Comic Sans MS, 28pt, bold, white
- Background: #FFA46B

### 3. Image Embedding
Supported formats: PNG, JPG, SVG (PDFs gracefully skipped due to PPTX format limitations)
- Automatically resolves figures from common folders: `Figures/`, `vis/`, `images/`
- Adds figure as full slide

### 4. Multi-Round Refinement
The `SlideRefiner` iteratively improves slide plans:
- Each round receives critique feedback from `SlideCritic`
- Tracks critique history across rounds
- Default 2 rounds; increase via `--rounds`

### 5. LLM Reflection (Optional)
The `StyleAgent.reflect_and_optimize()` runs advanced design critique:
- Calls `SlideCritic` iteratively
- Stops early if plan converges (no changes)
- Applies deterministic cleanup (text sanitization, bullet optimization, text wrapping)
- Enabled via `--use-reflection` flag

### 6. Text Optimization (Automatic)
- Removes LaTeX commands (`\thanks{}`, `\'e`, etc.)
- Strips emoji Unicode
- Converts Greek symbols (α, β) to readable text
- Splits overly long bullets into sub-bullets
- Wraps text to prevent slide overflow

### 7. Template Support
Pass an existing PPTX file with custom master slides, color schemes, and layouts:
- Master slide definitions are preserved
- Slide layouts are applied to generated slides
- Fallback to default layouts if template unavailable

```python
refined = refiner.refine(draft, rounds=3)  # 3 rounds of refinement
```

Each round:
- Receives the previous round's output as input
- Has access to critique history from all prior rounds
- Focuses on addressing remaining issues while building on past improvements
- Outputs a refined plan and brief critique summary

Default: 2 rounds. Increase `rounds` for more thorough optimization on complex sections.

---

## Aesthetic Design & Visual Styling

Every slide includes rich styling metadata for beautiful, professional rendering:

**Styling Fields:**
- `background_color`: Slide background color (hex, e.g., `"#FFFFFF"`)
- `text_color`: Primary text color (e.g., `"#333333"`)
- `accent_color`: Highlight/emphasis color (e.g., `"#2E7D32"`)
- `visual_type`: Slide category (`"technical"`, `"analogy"`, `"qa"`, `"intro"`, `"summary"`)
- `visual_emphasis`: Array of bullet indices to highlight for visual prominence
- `illustration_hint`: Optional suggestion for diagrams, icons, or visual aids

Styling fields are supported by the PPTX executor (simple, optional):
- `background_color`, `text_color`, `accent_color`, `visual_type` (`technical`, `analogy`, `qa`, etc.), and `visual_emphasis`.

Executors make best-effort use of these fields; if styling is missing the renderer falls back to a readable default.

---

MIT License
