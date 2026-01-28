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

---

## License

MIT License
