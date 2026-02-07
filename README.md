# TeX2Slides — Self-Reflective LLM Agent for Paper → Slides

TeX2Slides is a self-reflective LLM agent that converts a LaTeX research paper into
professional presentation slides, with a PPTX-first workflow.

Supported output:
- PowerPoint (PPTX) — primary and canonical renderer

The system follows a Planner → Reflector → Executor architecture:
- The LLM plans slide content
- The LLM reflects and improves its own output
- Deterministic executors generate the final slides
- No agent frameworks (AutoGen, LangGraph, n8n, etc.) are used

---

## Features

- Supports real multi-file LaTeX projects
  - Handles \input{} and \include{}
- LLM-based slide planning
- Self-reflection for quality improvement
-- Generates self-contained slides (not only oral-presentation slides)
-- PowerPoint generation using python-pptx
- Clear separation of reasoning and execution
- Fully controllable and auditable pipeline

---

## Agent Architecture

LaTeX Source (.tex)  
↓  
Parser (structure + figures)  
↓  
LLM Planner (draft slides)  
↓  
LLM Reflector (refinement)  
↓  
Final Slide Plan (JSON)  
↓  
Executor
- PowerPoint (.pptx)

The LLM never directly accesses files or tools.
It only produces structured JSON plans.

---

## Project Structure

```
tex2slides_agent/
├── main.py             # CLI (PPTX-first)
├── src/
│   ├── cli/
│   ├── parser/
│   ├── llm/
│   └── executors/      # includes pptx_executor (single backend)
├── pptx_executor.py    # top-level shim
├── requirements.txt
└── README.md
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

### Generate PowerPoint Slides (PPTX-first)

Usage:

```bash
python main.py --input path/to/main.tex --api-key YOUR_OPENAI_API_KEY --out paper_slides.pptx
```

Optional: export the generated PPTX to PDF using a headless LibreOffice if available:

```bash
python main.py --input path/to/main.tex --api-key YOUR_OPENAI_API_KEY --out paper_slides.pptx --export-pdf
```

If LibreOffice is not installed, the CLI will keep the PPTX output and report that PDF export was skipped.

### Example: Planner + Refiner (Professor / Teaching POV)

Use the `SlidePlanner` with a teaching perspective to produce slides tailored
for classroom instruction, then optionally pass the draft to `SlideRefiner`
to optimize pedagogical clarity.

Notes:
- All provided figures will be included unless they are absolutely irrelevant.
- For hard concepts, the planner will add an "analogy" slide immediately after
  the technical slide. Analogy slides are marked with `"analogy": true` and
  include an `"analogy_text"` field and `"analogy_color": "#FFDD00"` so
  executors can render them with a distinct highlight color that the
  professor can optionally skip or show.

Python snippet:

```python
from llm_agent import SlidePlanner, SlideRefiner

planner = SlidePlanner(api_key="YOUR_OPENAI_API_KEY")
refiner = SlideRefiner(api_key="YOUR_OPENAI_API_KEY")

draft = planner.plan(
    paper_title="Example Paper",
    section_title="Method",
    section_text="...",
    figures=[],
    include_all_figures=True,
    analogy_level="10-year-old",
)

refined = refiner.refine(draft, include_all_figures=True, analogy_level="10-year-old", rounds=2)
print(refined)
```

---

## Features: Q&A Slides & References

When using the professor perspective, the planner automatically includes Q&A slides and references.

- Q&A slides are marked with `"qa_slide": true` (or `"qa_text"`) and appear after major sections to prompt discussion.
- References are provided via a `"references"` array when applicable; each reference may be a string or an object with a `text` field.

The PPTX executor renders these slide types with graceful fallbacks and modest styling metadata.

---

## Multi-Round Reflection with Critique Memory

The `SlideRefiner` supports iterative refinement with **memory of past critiques**:

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
