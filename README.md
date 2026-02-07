# TeX2Slides — Self-Reflective LLM Agent for Paper → Slides

TeX2Slides is a self-reflective LLM agent that converts a LaTeX research paper into
high-quality presentation slides.

Supported outputs:
- Beamer (PDF)
- PowerPoint (PPTX)

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
- Generates self-contained slides (not only oral-presentation slides)
- Beamer to PDF via local compilation
- PowerPoint generation using python-pptx
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
- Beamer (.tex → PDF)  
- PowerPoint (.pptx)

The LLM never directly accesses files or tools.  
It only produces structured JSON plans.

---

## Project Structure

```
tex2slides_agent/
├── main.py
├── latex_parser.py
├── llm_agent.py
├── beamer_executor.py
├── pptx_executor.py
├── requirements.txt
└── README.md
```

---

## Input Format

Input must be the root LaTeX file of the paper
(the same file you would compile with pdflatex).

Examples:
- iclr2023_conference.tex
- ms.tex

Multi-file projects using \input{} are fully supported.

Do NOT pass:
- A directory
- Individual section files

---

## Installation

### Clone the repository
```bash
git clone https://github.com/<your-username>/tex2slides_agent.git
cd tex2slides_agent
```

### Install Python dependencies
```bash
pip install -r requirements.txt
```

### Install LaTeX (for Beamer)

macOS:
```bash
brew install --cask basictex
```

Add LaTeX to PATH:
```bash
echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify:
```bash
pdflatex --version
```

---

## Usage

### Generate Beamer Slides (PDF)

```bash
python main.py \
  --input path/to/main.tex \
  --api-key YOUR_OPENAI_API_KEY \
  --format beamer \
  --out paper_slides.tex
```

Compile to PDF:
```bash
pdflatex paper_slides.tex
pdflatex paper_slides.tex
open paper_slides.pdf
```

---

### Generate PowerPoint Slides

```bash
python main.py \
  --input path/to/main.tex \
  --api-key YOUR_OPENAI_API_KEY \
  --format pptx \
  --out paper_slides.pptx
```

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

refined = refiner.refine(draft, include_all_figures=True, analogy_level="10-year-old")
print(refined)
```

---

## Features: Q&A Slides & References

When using the professor perspective, the planner automatically includes:

- **Q&A Slides**: Marked with `"qa_slide": true`, these appear after major sections to prompt
  student discussion and reflection. Include a `"qa_text"` field with discussion prompts.

- **References & Citations**: Slides include a `"references"` array only when relevant. Each reference can be:
  - **Paper**: `{"type": "paper", "source": "Paper: Section X", "text": "..."}`
  - **External**: `{"type": "external", "source": "Source name", "text": "..."}`
  - **AI Recommendation**: `{"type": "ai_recommendation", "source": "AI-generated", "text": "..."}`
  
  References appear in smaller text at the bottom of slides. Paper citations take priority;
  AI-generated additions are clearly labeled so instructors can decide whether to include them.

---

MIT License
